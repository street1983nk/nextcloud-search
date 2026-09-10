# Die Kernaussage der Vergleichsmessung, als Blatt zum Entscheiden

Dieses Blatt ist nicht der Bericht. Es ist die kürzeste Fassung, auf der der
Owner entscheiden kann, solange die Box noch läuft. Jede Zahl nennt ihre
Rohdatei; eine Zahl ohne Rohdatei steht hier nicht, und wenn sie fehlt, steht
da, dass sie fehlt.

Gemessen am 09. und 10.09.2026 auf `i-06b1d913f5c6f669b`, einer AWS `m7g.large`
mit nativem arm64, 4 GB Maschinenspeicher, harte Containergrenze 2 GiB.
Verglichen wird gegen den Semantiklauf 06-11 vom 05.09. (v1.0) und die
Nachmessung vom 07.09.

---

## a. Die Store-Aussage, in der Form aus D-H2

**Der Indexaufbau über 52.111 Dokumente hat unter einer harten Grenze von
2 GiB keinen einzigen Prozess das Leben gekostet. Die drei Schadenszähler
`oom`, `oom_kill` und `oom_group_kill` stehen je auf null, die Heap-Spitze des
ganzen Laufs lag bei 1.764,2 MB, und der Zähler `max` steht auf 21.939.**

Was `max` bedeutet, in einem Satz: der Dateicache des Tantivy-Index lag gegen
die Grenze an, der Kernel hat ihn 21.939 mal zurückgedrängt, und kein Prozess
wurde dabei getötet. Der Zähler wird hier weder verschwiegen noch wegerklärt.

| Größe | 06-11 (v1.0) | Nachmessung 07.09. | **dieser Lauf** | Rohdatei |
|---|---|---|---|---|
| `oom` | 0 | 0 | **0** | `rohdaten/07-oom-beweis.txt` |
| `oom_kill` | 0 | 0 | **0** | `rohdaten/07-oom-beweis.txt` |
| `oom_group_kill` | 0 | 0 | **0** | `rohdaten/07-oom-beweis.txt` |
| `OOMKilled`, `RestartCount` | false, 0 | false, 0 | **false, 0** | `rohdaten/07-oom-beweis.txt` |
| höchster `anon` des Laufs | 1.837,8 MB (05:34:05Z) | 1.812,7 MB (05:55:53Z) | **1.764,2 MB (2026-09-10T08:12:24Z)** | `rohdaten/00-ende.txt`, aus `rohdaten/96-volllauf.csv` |
| `memory.events max` | 2.796 | 0 | **21.939** | `rohdaten/07-oom-beweis.txt` |
| `memory.peak` | 2.147.741.696 Byte | 1.990,3 MB | **2.147.483.648 Byte, gleich der harten Grenze** | `rohdaten/07-oom-beweis.txt` |
| `memory.current`-Spitze | 2.048,0 MB | 1.219,8 MB | **2.048,0 MB** | `rohdaten/00-ende.txt` |
| `sock_throttled` | 3.044 | 0 | **1.997** | `rohdaten/07-oom-beweis.txt` |
| harte Grenze | 2147483648 | dieselbe | **dieselbe, nach dem Neustart zurückgelesen** | `rohdaten/95-spitze-nachher.txt` |

Der Beweis ist **vor jedem Eingriff** erhoben. `07-oom-beweis.txt` trägt vier
Ablesungen: zwei vom Wächter am Ende beider Spuren (13:04:57Z und 13:05:11Z),
eine dritte am 10.09. um 13:48:08Z als erste Handlung dieses Plans, und eine
vierte um 14:46:22Z nach allen Messungen. Der bewusste Neustart des Containers
fand um 14:04:38Z statt, also nach den ersten drei.

**Ein Nebenbefund, der zu `max` gehört:** nach dem Neustart, über alle vier
Messblöcke dieses Plans hinweg, steht `max` auf **0**. Der Zähler gehört zum
Indexaufbau, nicht zum Suchbetrieb (`rohdaten/07-oom-beweis.txt`, vierte
Ablesung).

---

## b. MESS-01: die Grundlast im Leerlauf

| Größe | 06-11 | Nachmessung | **dieser Lauf** | Rohdatei |
|---|---|---|---|---|
| Grundlast im Leerlauf, `anon` | 691,8 MB | 693,4 MB | **103,2 MB** (108.199.936 Byte) | `rohdaten/94-grundlast.txt` |

**Differenz: minus 588,6 MB gegen 06-11.** Das ist besser als die gerechnete
Erwartung von 118 bis 150 MB.

**Wo der Unterschied anfällt: ausschließlich in der Grundlast.** Er trägt
nicht in die Suchphase und nicht in die Gesamtspitze durch:

- Die erste Suche kostet dieselben Gewichte wie vorher: `anon` 103,2 auf
  518,2 MB, also plus 415,0 MB, gegen plus 422,3 MB in der Nachmessung
  (`rohdaten/95-spitze-vorher.txt`).
- Die Gesamtspitze sinkt nur um 73,6 MB, von 1.837,8 auf 1.764,2 MB
  (`rohdaten/00-ende.txt`), obwohl die Grundlast um 588,6 MB gesunken ist.
  Wer 52.111 Dokumente indexiert, bezahlt die Spitze woanders.

---

## c. MESS-02, erste Hälfte: die p95-Reihe über fünf Stufen

Fünf Stufen, zehn Runden je Stufe, 410 Anfragen, keine einzige fehlgeschlagen,
über die OCS-Route und damit über den finalen PHP-Recheck
(`rohdaten/97-nebenlaeufigkeit.txt`, `rohdaten/97-stufe-<n>.json`).

| Nebenläufigkeit | Baseline p95 | **dieser Lauf p95** | Unterschied | Budget 2.500 ms |
|---|---|---|---|---|
| 1 | 481,6 ms | **464,3 ms** | minus 3,6 Prozent | gehalten |
| 4 | 1.009,4 ms | **1.068,0 ms** | **plus 5,8 Prozent** | gehalten |
| 8 | 1.915,0 ms | **2.125,5 ms** | **plus 11,0 Prozent** | gehalten |
| 12 | 3.045,4 ms | **3.453,4 ms** | **plus 13,4 Prozent** | gerissen |
| 16 | 3.782,7 ms | **4.446,2 ms** | **plus 17,5 Prozent** | gerissen |

**Die Zusage steht weiter auf Stufe 8, aber sie ist enger geworden:** 2.125,5 ms
sind **85,0 Prozent** des Budgets von 2.500 ms, gegen 76,6 Prozent in der
Baseline. Die Reserve schrumpft von 585,0 auf 374,5 ms.

`anon` und `memory.current` je Stufe: `anon` steht über alle fünf Stufen bei
1.521,5 bis 1.521,8 MB und wächst mit der Nebenläufigkeit **nicht**;
`memory.current` fällt von 1.752,3 auf 1.631,7 MB. Der Abstand zwischen beiden
liegt bei 110 bis 231 MB, in derselben Größenordnung wie die rund 86 MB der
Nachmessung (`rohdaten/97-nebenlaeufigkeit.txt`).

---

## d. MESS-02, zweite Hälfte: die zehn Sprachfälle

**Ergebnis: `sprachfaelle bestanden 6 von 10`, vier rote Fälle, neun rote
Zusicherungen** (`rohdaten/98-sprachfaelle.txt`).

Für diese zehn Fälle gibt es **keine v1.0-Entsprechung auf dieser Box**: weder
der Semantiklauf vom 05.09. noch die Nachmessung vom 07.09. hat sie gefahren.
Die Zahl ist eine **Erstmessung** und keine Vergleichszeile.

Die vier roten Fälle, im Wortlaut des Skripts:

| Fall | Was die Zusicherung verlangt | Was geschah |
|---|---|---|
| 1 | ein Kompositum über einen seiner Bestandteile gesucht bringt genau eine Datei | leere Trefferliste, vier Zusicherungen rot |
| 2 | `Frist` bringt genau die Kündigung zurück | leere Trefferliste |
| 4 | der Singular findet den Plural | leere Trefferliste |
| 6 | das Wort, das in zwei Dateien steht, bringt zwei Dateien | genau eine Datei, `09-bescheid.pdf` |

**Der Befund ist reproduziert und kein Messfehler.** Er wurde zweimal gefahren,
um Fallstrick 11 auszuschließen: Erstlauf 14:19:12Z bis 14:25:37Z
(`rohdaten/98-sprachfaelle-erstlauf.txt`), Nachmessung 14:35:02Z bis 14:41:27Z
(`rohdaten/98-sprachfaelle.txt`). Beide Läufe kommen auf dieselben 6 von 10,
dieselben vier Fälle, dieselben neun Zusicherungen.

**Und die Dateien, die die roten Fälle brauchen, liegen nachweislich im
Index.** Der Referenzkorpus des Sprachfall-Kontos ist vollständig verarbeitet:
26 indexiert, 7 übersprungen, 6 fehlgeschlagen, zusammen die 39 hochgeladenen
Dateien. Die drei Dateien der Fälle 1, 2 und 4 stehen als `indexed` in
`state.db`, mit 123, 148 und 132 Zeichen. Die sechs Fehlschläge sind die
absichtlich kaputten Dateien des Korpus (Nullbytes, abgeschnittener Trailer,
Seitenbaum-Zyklus und drei weitere), also erwartete Fälle und nicht der Grund.

Der CI-Lauf misst dieselben zehn Fälle grün, aber auf amd64 gegen eine frische
Instanz mit dem PHP-Entwicklungsserver; hier laufen sie auf arm64 gegen eine
All-in-One-Instanz mit vollem Vektorbestand. Gleich ist die Aussage, nicht die
Umgebung. Die Laufnummer des grünen CI-Laufs konnte das Skript nicht
feststellen und schreibt das so hin (`ci-beleg: der letzte gruene
integration.yml-Lauf ist unbekannt`). **Was diesen Unterschied verursacht,
beantwortet dieser Plan nicht.**

---

## e. Die übrigen Zahlen dieses Laufs

### Laufzeit und Durchsatz (`rohdaten/00-ende.txt`)

| Größe | 06-11 | **dieser Lauf** |
|---|---|---|
| beide Spuren bis zum letzten Vektor | 18 h 56 min | **26 h 37 min, plus 40,6 Prozent** |
| erste Spur allein | 18 h 04 min | **nicht messbar, die Spuren liefen gekoppelt** |
| Indexierung, über den ganzen Lauf | 45,7 je Minute | **31,6 je Minute** |
| Einbettung neben der OCR | rund 43 je Minute | **32,5 je Minute** |
| Einbettung allein, nach der ersten Spur | rund 170 je Minute | **kommt nicht vor** |

### Kaltstart auf vollem Bestand, DI-07-02 (`rohdaten/95-spitze-nachher.txt`)

| Größe | Vorwert | **dieser Lauf** |
|---|---|---|
| Kaltstart über OCS, eine Anfrage | 1.332,1 ms (07-01, leerer Bestand) | **1.838,4 ms** |
| Marge zur Aufrufdecke `REQUEST_TIMEOUT_SECONDS` = 1,5 s | plus 167,9 ms | **minus 338,4 ms** |
| dieselbe Größe auf leerem Bestand, 09.09. | , | 1.550,4 ms, Marge minus 50,4 ms |

**Die Decke von 1,5 s je Containeraufruf hält den Kaltstart auf vollem
Vektorbestand nicht aus.** Die eine gemessene Anfrage brachte **null Treffer**,
während dieselbe Route unmittelbar danach 18 Treffer auf drei Anfragen lieferte.
Dieser Plan entscheidet nicht über die Konstante; er liefert die Zahl.

### Seitenroute, Erstmessung (`rohdaten/99-seitenroute.txt`)

Vier Reihen à 20 Wiederholungen, beide Anmeldewege getrennt, Rangregel ohne
Interpolation. **Erstmessung und keine Vergleichszeile:** der Vorläuferbericht
maß auf einer Instanz **ohne** `vectors.db`, diese hat 146.171 Vektoren.

| Reihe | Anmeldeweg | p95 | Vorwert ohne Vektoren | Decke 1,5 s | Budget 3,0 s |
|---|---|---|---|---|---|
| A erste Seite | Sitzung | **0,332 s** | 0,122 s | Marge 1,168 s | Marge 2,668 s |
| B erste Seite | Basic-Auth | **0,775 s** | 0,445 s | Marge 0,725 s | Marge 2,225 s |
| C tiefe Seite | Sitzung | **0,333 s** | 0,122 s | Marge 1,167 s | Marge 2,667 s |
| D Dialogweg, limit=100 | Basic-Auth | **0,769 s** | 0,538 s | Marge 0,731 s | Marge 2,231 s |

Kein Ausreißer wurde entfernt. Das höchste Maximum steht bei Reihe D mit
0,825 s, das auffälligste bei Reihe A mit 0,445 s gegen einen p95 von 0,332 s.
Der Preis des Anmeldewegs, Differenz A gegen B am p95: **0,443 s**, gegen
0,318 s auf der Vergleichsinstanz.

### Rundenzählung des Rechteabgleichs, DI-07-03

| Fall | Runden je Suche | Containeraufrufe je Suche | p95 | Rohdatei |
|---|---|---|---|---|
| 1, der Alltag | **1,0** | **1,9** (10 Kandidaten-, 9 Snippetaufrufe) | 683,6 ms | `rohdaten/99b-runden-alltag.txt` |
| 2, provozierter Driftfall | 1,0 | 1,0 | 681,6 ms | `rohdaten/99b-runden-drift.txt` |

**Fall 2 ist keine Aussage über die Schleife, und das Skript sagt es selbst.**
Es liest dreiwertig: null Treffer **und** eine Runde je Suche heißt "der
Vorfilter wusste schon Bescheid, die Drift war zu kurz". Der Driftfall wurde
also nicht erzeugt. Die Alltagszahl trägt, die Driftzahl nicht.

### Bestand, Größe und Verdikte (`rohdaten/48-vektorbestand.txt`)

| Größe | 06-11 | **dieser Lauf** |
|---|---|---|
| indexiert / übersprungen / fehlgeschlagen | 51.961 / 37 / 0 | **52.111 / 37 / 0** |
| Chunks | 145.854 | **146.171** |
| Chunks je Dokument | 2,807 | **2,805** |
| `vectors.db` plus WAL | 68.642.504 Byte | **68.695.896 Byte** |
| Byte je Dokument | 1.321,0 | **1.318,3** |
| Tantivy-Index | 785.308.851 Byte | **786.506.160 Byte** |
| Byte je Dokument | 15.113 | **15.093** |
| Vektoranteil am Tantivy | 8,74 Prozent | **8,73 Prozent** |
| Zeichen im Korpus | 1.397.354.875 | **1.397.874.090** |

**Der Endungsvergleich stimmt in beiden Hälften überein:** 13 Endungen,
Generator gleich Bestand, **genau eine benannte Abweichung**, nämlich 20 `csv`
mit `skipped:too_large` aus der Kategorie `oversize`
(`rohdaten/66-generator-endungen.json` lokal aus dem Samen,
`rohdaten/68-bestand-endungen.json` über `state.db` auf der Box).

**Der Verdikt-Versatz plus 34 aus Plan 10-05 ist vollständig aufgeklärt**
(`rohdaten/48-vektorbestand.txt`). `state.db` führt 52.148 Zeilen auf zwei
Speichern: 52.099 im Baum des Lasttest-Kontos und 49 in einem zweiten Speicher,
dem Willkommenspaket eines zweiten Kontos, das der Dateizähler von Plan 10-05
nicht durchlaufen hat. Im Lasttest-Baum liegen 64 Skelettdateien, davon tragen
49 ein Verdikt; die übrigen 15 sind 10 `.whiteboard`, 4 `.odg` und 1 `.mp4`,
also Endungen, die nicht eingereiht werden. **52.114 minus 15 plus 49 ergibt
52.148, und der Versatz plus 34 ist genau 49 minus 15.**

---

## Was dieser Lauf nicht besser gemacht hat

Diese Überschrift steht **vor** der Owner-Frage und nicht danach. Jede Zeile
hier kommt aus einer Rohdatei dieses Verzeichnisses.

1. **Die Suchlatenz ist auf vier von fünf Stufen schlechter geworden, alle vier
   über dem Rauschband von fünf Prozent.** Stufe 4 plus 5,8, Stufe 8 plus 11,0,
   Stufe 12 plus 13,4, Stufe 16 plus 17,5 Prozent. Die Zusage auf Stufe 8 hält,
   aber ihre Reserve fällt von 585,0 auf 374,5 ms
   (`rohdaten/97-nebenlaeufigkeit.txt`, vier `regression stufe`-Zeilen).
2. **Der Lauf hat 40,6 Prozent länger gebraucht.** 26 h 37 min gegen 18 h 56 min,
   bei einem Mehrbestand von 0,29 Prozent. Er liegt über der Owner-Erwartung von
   22 bis 26 Stunden. Der Vorbehalt zieht in dieselbe Richtung: beim Anstoß
   lagen 1.653 Dateien schon im Index, ein Lauf von null hätte länger gebraucht
   (`rohdaten/00-ende.txt`).
3. **Der Durchsatz ist auf beiden Spuren gefallen**, und zwar gleichzeitig und
   um denselben Faktor: Indexierung 31,6 gegen 45,7 je Minute, Einbettung 32,5
   gegen rund 43 je Minute. Der Nachlauf mit rund 170 Dokumenten je Minute, der
   in 06-11 die letzten 52 Minuten trug, kommt nicht mehr vor
   (`rohdaten/00-ende.txt`).
4. **Der Kaltstart reißt die Aufrufdecke deutlicher als vorher.** 1.838,4 ms
   gegen eine Decke von 1.500 ms, Marge minus 338,4 ms, gegen plus 167,9 ms in
   Plan 07-01. Die eine gemessene Anfrage brachte null Treffer
   (`rohdaten/95-spitze-nachher.txt`).
5. **Vier von zehn Sprachfällen sind rot**, in zwei Läufen reproduziert, und die
   Dateien, die sie brauchen, liegen im Index. Es gibt keine v1.0-Entsprechung
   auf dieser Box, also ist es keine Verschlechterung gegen eine gemessene Zahl,
   aber es ist auch nicht das, was der grüne CI-Lauf verspricht
   (`rohdaten/98-sprachfaelle.txt`).
6. **`memory.events max` ist von 2.796 auf 21.939 gestiegen**, also um das
   7,8-fache, und `memory.peak` hat die harte Grenze exakt erreicht statt sie
   wie in der Nachmessung um 157 MB zu unterschreiten. Kein Prozess wurde
   getötet, aber der Kernel hat deutlich häufiger zurückgedrängt
   (`rohdaten/07-oom-beweis.txt`).
7. **Die `memory.current`-Spitze ist mit 2.048,0 MB genauso hoch wie in 06-11**,
   obwohl die Grundlast um 588,6 MB gesunken ist. Die Ersparnis der Grundlast
   trägt nicht in die Spitze durch (`rohdaten/00-ende.txt`).
8. **Der provozierte Driftfall ließ sich nicht herstellen.** DI-07-03 bekommt
   damit nur eine seiner zwei Zahlen belastbar
   (`rohdaten/99b-runden-drift.txt`).
9. **Zwei Messskripte waren fehlerhaft und mussten während des Laufs
   korrigiert werden.** Der `occ`-Wrapper in `99b-runden.sh` und
   `98-sprachfaelle.sh` reichte `OC_PASS` an nichts weiter, weil `sudo` die
   Umgebung räumt und `docker exec` keine weitergibt. Beide Fassungen unter
   `skripte/` sind die gefahrenen, mit einem Satz im Kopf.

Was besser wurde, damit das Blatt nicht schief steht: die Grundlast um
588,6 MB, die Gesamtspitze um 73,6 MB, Stufe 1 der Lastreihe um 3,6 Prozent,
`sock_throttled` von 3.044 auf 1.997, und die drei Schadenszähler stehen zum
dritten Mal in Folge auf null.

---

## f. Kosten und Stand

| Größe | Wert | Quelle |
|---|---|---|
| Box angefahren | 2026-09-09T09:20:06Z | `box.env`, `BOX_STARTED_ISO` |
| Stand dieses Blatts | 2026-09-10T14:50Z | , |
| Laufzeit bis hierher | **29,5 Stunden** | gerechnet aus `BOX_STARTED_ISO` |
| Kosten bis hierher | **3,42 USD netto** | 29,5 h mal 0,1158 USD je Stunde |
| Satz laufend | 0,1158 USD je Stunde | `aws_box.sh prices`, abgefragt 2026-09-04 |
| Satz angehalten | 0,3130 USD je Tag | `box.env`, `BOX_PARKED_COST_USD_PER_DAY` |
| Kostendeckel, ursprünglich | **30 Stunden und 3,50 USD** | Owner-Freigabe 09.09., `rohdaten/89-anfahrt.txt` |
| Kostendeckel, angehoben | **34 Stunden und 4,00 USD** | Owner am 2026-09-10, greift 2026-09-10T19:20Z |

Der ursprüngliche Deckel von 30 Stunden und 3,50 USD läuft am 2026-09-10 um
15:20:06Z aus. Der angehobene Deckel von 34 Stunden und 4,00 USD läuft am
2026-09-10 um 19:20:06Z aus. Jede weitere Stunde Laufzeit kostet 0,1158 USD.

**Ein Vorbehalt zu diesem Block, und er ist der Grund für eine Rückfrage:** die
Zahlen dieses Abschnitts sind aus `BOX_STARTED_ISO` und dem Stundensatz
gerechnet und nicht über `aws_box.sh status` von der API bestätigt. Die
AWS-Zugangsdaten liegen ausschließlich in der Umgebung und nicht auf dieser
Platte, also kann dieser Lauf weder `status` noch `stop` ausführen. Der
Kostenblock wird nach dem Anhalten aus `box.env` nachgetragen.
