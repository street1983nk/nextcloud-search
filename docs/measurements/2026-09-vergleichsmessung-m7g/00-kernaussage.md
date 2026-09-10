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
integration.yml-Lauf ist unbekannt`).

### Und die Diagnose auf Owner-Entscheid vom 10.09.: es ist nicht die Sprache

Der Owner hat entschieden, die roten Befunde nachzumessen, solange die Box
läuft. Das Ergebnis steht in `rohdaten/98b-sprachfaelle-diagnose.txt` und es
ändert die Deutung dieser sechs von zehn grundlegend.

**Die deutsche Analysekette tut, was sie soll, und das ist gemessen.**
`Grundstücksverkehrsgenehmigung` wird zu `grundstuck`, `verkehr`, `genehm`, die
Anfrage `Genehmigung` wird zu `genehm`, und beide teilen dieses Token.
Dasselbe gilt für `Kündigungsfrist` gegen `Frist` und für `Verträge` gegen
`Vertrag`. Alle drei Tokens stehen im Feld `body_de` des Index mit Dokumenten
daran, und jede der vier Suchen liefert im Index zehn Treffer.

**Der Grund ist die Kandidatenliste, und der Messaufbau hat ihn erzeugt.** Die
zehn Treffer gehören samt und sonders dem Lasttest-Konto mit seinen 52.111
Dokumenten und keiner dem Konto, das gefragt hat. Für `Genehmigung`, `Frist`
und `Vertrag` kommt unter den ersten **zweitausend** Kandidaten keine einzige
Datei des fragenden Kontos vor; für `Bescheid` steht sie auf **Rang 1.925 von
2.000**. Der Vorfilter rankt über den ganzen Index, der Recheck filtert erst
danach auf das Erlaubte, und dann ist nichts mehr übrig. Die sechs grünen Fälle
sind genau die, deren Begriffe im Lastkorpus selten sind: `Mueller` hat im
ganzen Index einen einzigen Treffer, und das ist die eigene Datei.

Das ist Fallstrick 3 in einer Form, die der Skriptkopf nicht abdeckt: er führt
den eigenen Nutzer ein, weil der Lastkorpus dieselben Wörter trägt, aber ein
eigener Nutzer trennt die Berechtigung und nicht den Index.

**Was trotzdem ein Befund über das Erzeugnis ist,** und er gehört zu DI-07-03:
auf einer Instanz mit großem Fremdbestand findet ein Nutzer mit wenigen Dateien
seine eigenen nicht, sobald seine Begriffe im Fremdbestand häufig sind, und er
bekommt keine Fehlermeldung, sondern eine leere Liste. Die Rundenzählung dieses
Plans hat 1,0 Runde je Suche gemessen: die Schleife holt keine zweite Runde
nach, obwohl der Recheck alle Kandidaten der ersten verworfen hat.

**Die Bilanz 6 von 10 bleibt stehen, weil sie gemessen ist. Sie ist aber keine
Aussage über die Sprachverarbeitung von v1.1 und darf im Bericht nicht als eine
geführt werden.**

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

### Die Reproduktion auf Owner-Entscheid vom 10.09., und was sie zutage fördert

Drei weitere Neustarts mit drei Begriffen, dazu das Nextcloud-Protokoll
(`rohdaten/95b-kaltstart-reproduktion.txt`,
`rohdaten/95c-kaltstart-reproduktion-teil2.txt`).

| Durchgang | Begriff | Kaltstart | Marge zu 1,5 s | Treffer | warm |
|---|---|---|---|---|---|
| 1 | Bescheid | 1.598 ms | minus 98 ms | **6** | 560 bis 566 ms |
| 2 | Vertrag beenden | 1.805 ms | minus 305 ms | **6** | 662 bis 674 ms |
| 3 | Kuendigung | 2.468 ms | minus 968 ms | **6** | 553 bis 565 ms |

**Die null Treffer ließen sich nicht reproduzieren, aber das Protokoll belegt
sie trotzdem.** Um `2026-09-10T14:05:17Z`, dem Zeitpunkt der Kaltstartmessung,
mit dem Begriff `Vertrag beenden`, den `search_load.py` bei einer Runde als
`TERMS[0]` stellt, steht dort:

```
app_api:  cURL error 28: Operation timed out after 1501 milliseconds
          with 0 bytes received ... /exapps/findling_backend/search
findling: Findling: backend unreachable
```

**Warum die Reproduktion trotzdem Treffer lieferte, und warum sich die Zahlen
nicht widersprechen:** die 1.838,4 ms und die 1.598 bis 2.468 ms messen die
ganze OCS-Anfrage, die Decke von 1.501 ms gilt nur für den Containeraufruf
darin. In den drei Durchgängen blieb er darunter, weil der Seitencache des
Wirts die Modellgewichte der vorigen Starts noch hielt; um 14:05:17Z lag der
letzte Start 29 Stunden zurück. **Eine Gesamtdauer über 1,5 s ist also kein
Beweis für einen Abbruch, und eine darunter keiner für das Gegenteil.**

### Der Befund, der bei dieser Reproduktion abgefallen ist, und er ist der größere

Dasselbe Protokoll zählt zwischen `13:51:11Z` und `13:51:42Z` **siebzehn
abgebrochene Containeraufrufe**. Dieses Fenster ist **Stufe 16 der
Nebenläufigkeitsreihe** (13:50:59Z bis 13:51:42Z), und `97-stufe-16.json`
meldet `"failures": 0` für 160 Anfragen. Die Route antwortet bei einem
abgebrochenen Containeraufruf mit HTTP 200 und einer Ergebnisgruppe ohne
Containerteil, also zählt das Lastwerkzeug sie als beantwortet.

| Stufe | Anfragen | failures | Treffer | Treffer je Anfrage | Abbrüche im Fenster |
|---|---|---|---|---|---|
| 1 | 10 | 0 | 54 | 5,40 | 0 |
| 4 | 40 | 0 | 216 | 5,40 | 0 |
| 8 | 80 | 0 | 420 | 5,25 | 0 |
| 12 | 120 | 0 | 577 | 4,81 | 0 |
| 16 | 160 | 0 | 666 | **4,16** | **17** |

**Für 10,6 Prozent der Anfragen der Stufe 16 hat die gemessene Antwortzeit
nicht die Zeit einer vollständigen Antwort gemessen.** Die Stufen 1 bis 12 sind
davon nicht berührt, und die Zusage steht auf Stufe 8. Die 4.446,2 ms der Stufe
16 sind eher zu günstig als zu schlecht.

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
5. **Ein Nutzer mit wenigen Dateien findet sie neben einem großen Fremdbestand
   nicht**, und er bekommt dabei keine Fehlermeldung, sondern eine leere Liste.
   Für drei von vier geprüften Begriffen kommt seine Datei unter den ersten
   2.000 Kandidaten nicht vor, weil der Vorfilter über den ganzen Index rankt
   und der Recheck erst danach filtert. Die Schleife holt keine zweite Runde
   nach (1,0 Runde je Suche, gemessen). Das ist der Befund hinter den vier
   roten Sprachfällen und er gehört zu DI-07-03
   (`rohdaten/98b-sprachfaelle-diagnose.txt`, `rohdaten/99b-runden-alltag.txt`).
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
10. **Das Lastwerkzeug meldet null Fehlschläge, wo siebzehn Containeraufrufe
    abgebrochen sind.** In Stufe 16 der Reihe stehen im Nextcloud-Protokoll 17
    Abbrüche mit `cURL error 28` bei 160 Anfragen, während
    `97-stufe-16.json` `"failures": 0` schreibt. Die Route antwortet bei einem
    abgebrochenen Containeraufruf mit HTTP 200 und ohne Containerteil. Der
    Fingerabdruck steht in den Trefferzahlen: 5,40 je Anfrage auf den Stufen 1
    und 4, nur 4,16 auf Stufe 16. Ein Messwerkzeug, das einen Ausfall als
    Erfolg zählt, ist der unangenehmere Befund von beiden
    (`rohdaten/95c-kaltstart-reproduktion-teil2.txt`).

Was besser wurde, damit das Blatt nicht schief steht: die Grundlast um
588,6 MB, die Gesamtspitze um 73,6 MB, Stufe 1 der Lastreihe um 3,6 Prozent,
`sock_throttled` von 3.044 auf 1.997, und die drei Schadenszähler stehen zum
dritten Mal in Folge auf null.

---

## f. Kosten und Stand

| Größe | Wert | Quelle |
|---|---|---|
| Box angefahren | 2026-09-09T09:19:50Z | `aws_box.sh status` |
| Stand dieses Blatts | 2026-09-10T15:52Z | `aws_box.sh status` |
| Laufzeit bis hierher | **30,4 Stunden** | `rohdaten/93-kosten-und-verbleib.txt` |
| Kosten bis hierher | **3,53 USD netto** | dieselbe Datei, aus der API |
| Satz laufend | 0,1158 USD je Stunde (0,0978 Box, 0,0130 Speicher, 0,0050 Adresse) | `aws_box.sh prices`, abgefragt 2026-09-04 |
| Satz angehalten | 0,3130 USD je Tag | `box.env`, `BOX_PARKED_COST_USD_PER_DAY` |
| Kostendeckel, ursprünglich | **30 Stunden und 3,50 USD** | Owner-Freigabe 09.09., `rohdaten/89-anfahrt.txt` |
| Kostendeckel, angehoben | **34 Stunden und 4,00 USD** | Owner am 2026-09-10, greift 2026-09-10T19:20Z |

**Der ursprüngliche Deckel von 30 Stunden und 3,50 USD ist gerissen**, und zwar
am 2026-09-10 um 15:20Z. Der Owner hat ihn vor Beginn der Messungen dieses
Plans auf 34 Stunden und 4,00 USD angehoben; er greift am 2026-09-10 um
19:20Z. Stand bei Abfassung dieses Blatts: 30,4 von 34 Stunden, 3,53 von
4,00 USD.

### Nachtrag vom 2026-09-10, nach der Berichtsabnahme: die Box ist angehalten

Der Owner hat den Bericht am 2026-09-10 abgenommen. Danach ist
`scripts/ops/aws_box.sh stop` gefahren worden. Die vier Schlüssel, die dieser
Aufruf selbst in `box.env` schreibt, und die Abschlusszahlen:

| Größe | Wert |
|---|---|
| `BOX_STOPPED_ISO` | **2026-09-10T16:22:50Z** |
| `BOX_LAST_UPTIME_HOURS` | **31.05** |
| `BOX_LAST_UPTIME_COST_USD` | **3.5969** |
| `BOX_PARKED_COST_USD_PER_DAY` | 0.3130, gilt unverändert |
| Zustand, aus der API um 16:23:15Z | **stopped**, nicht running |
| gegen den angehobenen Deckel | **31,05 von 34 Stunden, 3,5969 von 4,00 USD**, also nicht gerissen |

**Der Verbleib: angehalten, nicht abgebaut.** Beide Datenträger bleiben, mit
Korpus, beiden Indizes und den Abbildern. Der Abbau ist ausdrücklich nicht
gefahren worden; er ist ein eigener Entscheid und braucht einen eigenen Plan in
Phase 11. Ein Stop gibt die öffentliche Adresse zurück, also sind `BOX_IP` und
der A-Record `loadtest.infranode.dev` bis zum nächsten Start veraltet.

Der ausführliche Nachtrag mit der API-Feststellung steht in
`rohdaten/93-kosten-und-verbleib.txt`, Abschnitt 7.

**Wo die Zeit hingegangen ist:** nicht in die Messungen, sondern in den
Indexaufbau. Der Volllauf brauchte 26 h 37 min statt der erwarteten rund
19 Stunden, also 7 h 37 min mehr als geplant. Die Anfahrt und die Messungen vor
dem Lauf kosteten 38 Minuten, alle Messungen nach dem Lauf einschließlich der
beiden vom Owner entschiedenen Nachmessungen rund 2 h 50 min.

---

## g. Die Entscheidungen des Owners vom 2026-09-10, wortgetreu

Der Checkpoint dieses Plans ist am **2026-09-10** mit dem Signal "zahlen
abgenommen" beantwortet worden. Die Antworten, wortgetreu und mit Datum:

| Frage | Antwort des Owners, wortgetreu | Datum |
|---|---|---|
| Tragen die vier Kernzahlen? | "ZAHLEN ABGENOMMEN: die vier Kernzahlen tragen (Grundlast 103,2 MB, anon 1.764,2 MB, max=21.939 mit Einordnung Indexaufbau, p95 Stufe 8 = 2.125,5 ms)." | 2026-09-10 |
| Offene Frage 5, `CLAUDE.md` | "JA, Umsetzung in 10-07 wie vorgeschlagen; dieser Plan fasst CLAUDE.md nicht an." | 2026-09-10 |
| Offene Frage 7, Abbau der Box | "NUR ANHALTEN, kein Abbau (0,3130 USD/Tag geparkt akzeptiert). Abbau ist ein eigener Entscheid in Phase 11." | 2026-09-10 |
| Zeitpunkt des Anhaltens | "die Box LAEUFT WEITER BIS ZUR BERICHTSABNAHME (10-07)." | 2026-09-10 |
| Punkt 7, die roten Befunde | "JETZT NACHMESSEN, solange die Box laeuft." | 2026-09-10 |

**Was daraus folgt, und was ausdrücklich nicht:**

- `CLAUDE.md` ist von diesem Plan **nicht angefasst** worden. Die Zeile
  "Tokenizer und Splitter, 544 MB" gehört in die RAM-Budget-Tabelle und wird in
  **Plan 10-07** eingetragen.
- Die Box ist **nicht angehalten**. `aws_box.sh stop` gehört nach der
  Berichtsabnahme in **Plan 10-07**, zusammen mit dem Nachtrag der vier
  Schlüssel aus `box.env`.
- Der **Abbau ist als Auftrag für Phase 11 festgehalten**, mit Datum
  2026-09-10, und er ist in diesem Plan nicht gefahren worden. Er braucht einen
  eigenen Plan mit eigener Freigabe, der Nichtexistenz-Prüfung für Instanz,
  Datenträger und Security Group und dem Sweep nach dem Tag
  `purpose=findling-phase5`.
- Die zwei Nachmessungen sind gefahren, ihre Rohdaten liegen im Verzeichnis,
  und ihre Ergebnisse stehen oben in den Abschnitten d und e. **Beide haben die
  Deutung der Zahlen verändert, keine von beiden die Zahlen selbst.**
