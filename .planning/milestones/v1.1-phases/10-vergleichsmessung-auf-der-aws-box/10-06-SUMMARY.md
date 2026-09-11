---
phase: 10-vergleichsmessung-auf-der-aws-box
plan: 06
subsystem: messung
tags: [messung, mess-01, mess-02, mess-03, di-07-02, di-07-03, aws-box, arm64]
requires:
  - "10-05: der fertige Volllauf, seine Rohdaten und der OOM-Beweis des Waechters"
  - "die laufende Box i-06b1d913f5c6f669b mit unangetastetem Container"
provides:
  - "der OOM-Beweis in vier Ablesungen, vor jedem Eingriff erhoben"
  - "die p95-Reihe ueber fuenf Nebenlaeufigkeitsstufen, 410 Anfragen"
  - "der Kaltstart auf vollem Vektorbestand, DI-07-02"
  - "die Rundenzaehlung des Rechteabgleichs im Alltagsfall, DI-07-03"
  - "die Seitenroute als Erstmessung auf einer Instanz mit vectors.db"
  - "die zehn Sprachfaelle mit ihrer Diagnose"
  - "das Kernaussage-Blatt 00-kernaussage.md mit jeder Verschlechterung"
affects:
  - "10-07: der Bericht, das Anhalten der Box, die CLAUDE.md-Zeile"
  - "Phase 11: der Abbau der Box, MAX_ROUNDS, REQUEST_TIMEOUT_SECONDS"
tech-stack:
  added: []
  patterns:
    - "Rohdaten byteidentisch beidseitig per sha256 geprueft, bevor sie committet werden"
    - "Protokollzeilen vor dem Commit auf ihre Felder gekuerzt, weil sie Nutzerinhalte tragen"
key-files:
  created:
    - "docs/measurements/2026-09-vergleichsmessung-m7g/00-kernaussage.md"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/07-oom-beweis.txt"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/00-ende.txt"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/48-vektorbestand.txt"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/97-nebenlaeufigkeit.txt"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/95-spitze-nachher.txt"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/95b-kaltstart-reproduktion.txt"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/95c-kaltstart-reproduktion-teil2.txt"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/98b-sprachfaelle-diagnose.txt"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/93-kosten-und-verbleib.txt"
  modified:
    - "docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/skripte/99b-runden.sh"
    - "docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh"
decisions:
  - "Der OOM-Beweis wurde ein drittes Mal erhoben, obwohl der Waechter ihn zweimal geschrieben hatte: zwischen seiner Ablesung und dem Beginn dieses Plans lagen 43 Minuten Containerleben"
  - "Die Reihenfolge der Messbloecke wurde auf 11, 12, 10 gedreht, weil die Sprachfaelle 46 Minuten Wartefrist kosten und der Kostendeckel lief"
  - "Die vier roten Sprachfaelle sind auf Owner-Entscheid diagnostiziert worden statt als Befund berichtet, und die Diagnose hat ihre Deutung umgedreht"
  - "Die Box wird auf Owner-Entscheid NICHT angehalten; aws_box.sh stop wandert an Plan 10-07"
metrics:
  duration: "2 h 10 min aktiv, davon rund 50 min Messzeit auf der Box"
  completed: 2026-09-10
---

# Phase 10 Plan 06: Die Nach-Messungen auf der laufenden Box, Summary

Alle Zahlen, die nur am Container dieses Laufs zu holen waren, sind erhoben, in
der Reihenfolge, die sie gueltig macht: der OOM-Beweis zuerst und vor jedem
Eingriff, die Lastreihe auf dem warmen Container, der Kaltstart nach einem
bewussten Neustart. Zwei der drei auffaelligsten Befunde haben sich unter der
vom Owner entschiedenen Nachmessung als etwas anderes entpuppt, als sie
zunaechst aussahen, und der dritte ist bei dieser Nachmessung erst aufgefallen.

## Accomplishments

- **Der OOM-Beweis traegt vier Ablesungen und keine davon liegt hinter einem
  Neustart.** Der Waechter schrieb zwei (13:04:57Z und 13:05:11Z), dieser Plan
  erhob als allererste Handlung eine dritte um **13:48:08Z** und nach allen
  Messungen eine vierte um 14:46:22Z. Der bewusste Neustart fand um 14:04:38Z
  statt, also nach den ersten drei. `oom`, `oom_kill` und `oom_group_kill`
  stehen je auf **0**, `OOMKilled=false`, `RestartCount=0`, `max` auf **21.939**
  gegen 2.796 in 06-11, `memory.peak` genau auf der harten Grenze von
  2.147.483.648 Byte.
- **Ein Nebenbefund, der `max` einordnet und den der Owner uebernommen hat:**
  nach dem Neustart, ueber alle vier Messbloecke dieses Plans, steht `max` auf
  **0**. Der Zaehler gehoert zum Indexaufbau und nicht zum Suchbetrieb.
- **Die p95-Reihe liegt vor, 410 Anfragen, keine gemeldete fehlgeschlagen.**
  464,3 / 1.068,0 / 2.125,5 / 3.453,4 / 4.446,2 ms gegen 481,6 / 1.009,4 /
  1.915,0 / 3.045,4 / 3.782,7 ms. Die Zusage steht weiter auf Stufe 8, aber ihre
  Reserve faellt von 585,0 auf 374,5 ms, also von 76,6 auf **85,0 Prozent** des
  Budgets. Vier Stufen tragen eine `regression stufe`-Zeile, alle vier ueber dem
  Rauschband.
- **Die Spitzen sind je Phase gerechnet, mit Grenzen aus der Statusreihe und
  nicht aus einer Schaetzung.** Hoechster `anon` **1.764,2 MB um
  2026-09-10T08:12:24Z**, also der niedrigste der drei Laeufe. Der Besitzer der
  Spitze ist von der Phase der ersten Suche in die Phase mit OCR gewandert, wie
  schon in der Nachmessung. `memory.current` erreicht 2.048,0 MB, genau wie in
  06-11, obwohl die Grundlast um 588,6 MB gesunken ist.
- **Der Verdikt-Versatz plus 34 aus Plan 10-05 ist restlos aufgeklaert.**
  `state.db` fuehrt 52.148 Zeilen auf zwei Speichern: 52.099 im Baum des
  Lasttest-Kontos und 49 in einem zweiten, dem Willkommenspaket eines zweiten
  Kontos, das der Dateizaehler nicht durchlief. Im Lasttest-Baum liegen 64
  Skelettdateien, davon tragen 49 ein Verdikt; die uebrigen 15 sind 10
  `.whiteboard`, 4 `.odg` und 1 `.mp4`. **52.114 minus 15 plus 49 ergibt 52.148,
  und plus 34 ist genau 49 minus 15.**
- **Der Endungsvergleich stimmt in beiden Haelften:** 13 Endungen, Generator
  gleich Bestand, genau eine benannte Abweichung (20 csv `too_large`).
- **DI-07-02 hat seine Zahl, und sie ist unangenehm:** Kaltstart auf vollem
  Bestand **1.838,4 ms**, Marge zur 1,5-s-Decke **minus 338,4 ms** gegen plus
  167,9 ms in Plan 07-01.
- **DI-07-03 hat eine belastbare Zahl und eine ehrlich als nicht belastbar
  ausgewiesene:** Fall 1 mit 1,0 Runde und 1,9 Containeraufrufen je Suche; Fall
  2 liess sich nicht erzeugen, und das Skript liest das selbst dreiwertig.
- **Die Seitenroute ist zum ersten Mal auf einer Instanz mit `vectors.db`
  gemessen** und ausdruecklich als Erstmessung ausgewiesen: p95 0,332 / 0,775 /
  0,333 / 0,769 s, alle vier unter der Aufrufdecke und dem Seitenbudget.
- **Das Kernaussage-Blatt liegt vor, und die Verschlechterungen stehen darauf,
  bevor die Frage gestellt wurde.** Zehn Posten unter "Was dieser Lauf nicht
  besser gemacht hat", jeder mit seiner Rohdatei.
- **Die zwei Nachmessungen, die der Owner entschieden hat, haben zwei Deutungen
  umgedreht und einen dritten Befund erst zutage gefoerdert.** Sie stehen unten
  in einem eigenen Abschnitt, weil sie der eigentliche Ertrag dieses Plans sind.

## Task Commits

1. **Task 1: OOM-Beweis, Laufzeit, Spitzen je Phase, p95-Reihe** , `a13c6ce` (feat)
2. **Task 2: Kaltstart, Seitenroute, Rundenzaehlung, Sprachfaelle** , `0a9b538` (feat)
3. **Task 3: Kernaussage-Blatt und abgeschlossener Ablaufplan** , `c553980` (docs)
4. **Task 4/5: die zwei Nachmessungen auf Owner-Entscheid** , `8045852` (feat)
5. **Task 4/5: Owner-Entscheide, Nachmessungen im Blatt, Kosten und Verbleib** , `9f64aa3` (docs)

## Die zwei Nachmessungen, und warum sie den Bericht retten

Der Owner hat am 10.09. entschieden, die roten Befunde nachzumessen, solange
die Box laeuft. Das war die richtige Entscheidung, und zwar aus einem Grund,
den vorher niemand nennen konnte: **beide Befunde bedeuteten etwas anderes, als
sie aussahen, und ein Bericht ohne diese Diagnose haette zwei falsche Aussagen
getragen.**

### 1. Die vier roten Sprachfaelle sind kein Sprachdefekt

`rohdaten/98b-sprachfaelle-diagnose.txt`

Die Bilanz `sprachfaelle bestanden 6 von 10` war in zwei Laeufen reproduziert
(14:19Z und 14:35Z, dieselben vier Faelle, dieselben neun Zusicherungen), und
die drei Dateien der roten Faelle standen nachweislich als `indexed` in
`state.db`. Das sah nach einem Defekt der Sprachverarbeitung aus.

**Es ist keiner, und das ist gemessen.** Die deutsche Kette zerlegt
`Grundstuecksverkehrsgenehmigung` mit echtem Umlaut zu `grundstuck`, `verkehr`,
`genehm`, die Anfrage `Genehmigung` zu `genehm`; beide teilen dieses Token.
Dasselbe gilt fuer `Kuendigungsfrist` gegen `Frist` und `Vertraege` gegen
`Vertrag`. Alle drei Tokens stehen im Feld `body_de` mit Dokumenten daran, und
jede der vier Suchen liefert im Index zehn Treffer.

**Der Grund ist die Kandidatenliste.** Die zehn Treffer gehoeren samt und
sonders dem Lasttest-Konto mit 52.111 Dokumenten und keiner dem Konto, das
gefragt hat. Fuer `Genehmigung`, `Frist` und `Vertrag` kommt unter den ersten
**zweitausend** Kandidaten keine Datei des fragenden Kontos vor; fuer
`Bescheid` steht sie auf **Rang 1.925 von 2.000**. Die sechs gruenen Faelle
sind genau die, deren Begriffe im Lastkorpus selten sind: `Mueller` hat im
ganzen Index einen einzigen Treffer, und das ist die eigene Datei.

Das ist Fallstrick 3 in einer Form, die der Skriptkopf nicht abdeckt: er fuehrt
den eigenen Nutzer ein, weil der Lastkorpus dieselben Woerter traegt, aber ein
eigener Nutzer trennt die **Berechtigung** und nicht den **Index**.

**Was trotzdem ein Befund ueber das Erzeugnis ist, und er gehoert zu
DI-07-03:** auf einer Instanz mit grossem Fremdbestand findet ein Nutzer mit
wenigen Dateien seine eigenen nicht, sobald seine Begriffe im Fremdbestand
haeufig sind, und er bekommt keine Fehlermeldung, sondern eine leere Liste. Die
Rundenzaehlung dieses Plans hat 1,0 Runde je Suche gemessen: die Schleife holt
keine zweite Runde nach, obwohl der Recheck alle Kandidaten der ersten
verworfen hat.

### 2. Der Kaltstart mit null Treffern ist belegt, aber nicht reproduzierbar

`rohdaten/95b-kaltstart-reproduktion.txt`, `rohdaten/95c-kaltstart-reproduktion-teil2.txt`

Drei weitere Neustarts mit drei Begriffen: Kaltstartdauern 1.598, 1.805 und
2.468 ms, alle drei ueber der Decke von 1.500 ms, und alle drei mit **sechs
Treffern**. Wer nur diese Tabelle liest, schliesst, die null Treffer seien ein
Einzelfall gewesen und die Decke schneide nichts ab.

**Das Protokoll sagt etwas anderes, und zwar fuer genau die fragliche
Anfrage.** Um `2026-09-10T14:05:17Z`, mit dem Begriff `Vertrag beenden`, den
`search_load.py` bei einer Runde als `TERMS[0]` stellt, steht dort
`cURL error 28: Operation timed out after 1501 milliseconds with 0 bytes
received` und `Findling: backend unreachable`. Der Containeraufruf ist in die
Decke gelaufen, und deshalb kamen null Treffer.

**Warum die Reproduktion trotzdem Treffer lieferte:** die 1.838,4 ms und die
1.598 bis 2.468 ms messen die ganze OCS-Anfrage, die Decke von 1.501 ms gilt
nur fuer den Containeraufruf darin. In den drei Durchgaengen blieb er darunter,
weil der Seitencache des Wirts die Modellgewichte der vorigen Starts noch
hielt; um 14:05:17Z lag der letzte Start 29 Stunden zurueck. **Eine
Gesamtdauer ueber 1,5 s ist kein Beweis fuer einen Abbruch, und eine darunter
keiner fuer das Gegenteil.** Diese Unterscheidung fehlte allen bisherigen
Kaltstartzahlen dieses Projekts.

### 3. Der Befund, der dabei abgefallen ist, und er ist der groesste

Dasselbe Protokoll zaehlt zwischen `13:51:11Z` und `13:51:42Z` **siebzehn
abgebrochene Containeraufrufe**. Dieses Fenster ist **Stufe 16 der
Nebenlaeufigkeitsreihe** (13:50:59Z bis 13:51:42Z), und `97-stufe-16.json`
meldet `"failures": 0` fuer 160 Anfragen. Die Route antwortet bei einem
abgebrochenen Containeraufruf mit HTTP 200 und einer Ergebnisgruppe ohne
Containerteil, also zaehlt das Lastwerkzeug sie als beantwortet.

| Stufe | Anfragen | failures | Treffer | Treffer je Anfrage | Abbrueche im Fenster |
|---|---|---|---|---|---|
| 1 | 10 | 0 | 54 | 5,40 | 0 |
| 4 | 40 | 0 | 216 | 5,40 | 0 |
| 8 | 80 | 0 | 420 | 5,25 | 0 |
| 12 | 120 | 0 | 577 | 4,81 | 0 |
| 16 | 160 | 0 | 666 | **4,16** | **17** |

Fuer **10,6 Prozent** der Anfragen der Stufe 16 hat die gemessene Antwortzeit
nicht die Zeit einer vollstaendigen Antwort gemessen. Die Stufen 1 bis 12 sind
davon nicht beruehrt und die Zusage steht auf Stufe 8; die 4.446,2 ms der Stufe
16 sind eher zu guenstig als zu schlecht. **Ein Messwerkzeug, das einen Ausfall
als Erfolg zaehlt, ist der unangenehmere der beiden Befunde**, und er waere
ohne die vom Owner entschiedene Nachmessung nicht aufgefallen.

## Task 4: Der Checkpoint und die fuenf Antworten

Resume-Signal am **2026-09-10**, Wortlaut "zahlen abgenommen". Die Antworten
stehen wortgetreu mit Datum in `00-kernaussage.md`, Abschnitt g:

1. **Die vier Kernzahlen tragen** (Grundlast 103,2 MB, `anon` 1.764,2 MB, `max`
   21.939 mit der Einordnung Indexaufbau, p95 Stufe 8 2.125,5 ms).
2. **Offene Frage 5, `CLAUDE.md`: JA**, Umsetzung in Plan 10-07. Dieser Plan
   hat `CLAUDE.md` nicht angefasst, `git diff` belegt es.
3. **Offene Frage 7, Abbau: NUR ANHALTEN**, kein Abbau. Als Auftrag fuer
   Phase 11 mit Datum festgehalten, samt Nichtexistenz-Pruefung und dem Tag
   `purpose=findling-phase5`.
4. **Zeitpunkt: die Box laeuft weiter bis zur Berichtsabnahme** in Plan 10-07.
5. **Punkt 7: jetzt nachmessen**, solange die Box laeuft. Ergebnis oben.

## Task 5 im angepassten Umfang

Der Plan sieht diesen Fall selbst vor: "Hat der Owner in Task 4 fuer
Weiterlaufen bis zur Berichtsabnahme entschieden, wird dieser Task erst nach
jener Abnahme gefahren." Die Reihenfolge der Plaene bleibt unveraendert, nur
der Stop-Befehl wandert an 10-07.

`rohdaten/93-kosten-und-verbleib.txt` traegt statt des Anhaltens den Stand aus
der API, den Owner-Entscheid wortgetreu und die Uebergabe an 10-07:

| Groesse | Wert |
|---|---|
| Zustand | **running**, ausdruecklich nicht stopped |
| Laufzeit | **30,4 Stunden** seit 2026-09-09T09:19:50Z |
| Kosten | **3,53 USD netto** |
| Satz | 0,1158 USD je Stunde (0,0978 Box, 0,0130 Speicher, 0,0050 Adresse) |
| Deckel, urspruenglich | 30 h und 3,50 USD, **gerissen am 15:20Z** |
| Deckel, angehoben | 34 h und 4,00 USD, greift 19:20Z |

**Wo die Zeit hingegangen ist:** nicht in die Messungen, sondern in den
Indexaufbau. Der Volllauf brauchte 26 h 37 min statt der erwarteten rund 19
Stunden. Anfahrt und Vormessungen kosteten 38 Minuten, alle Nachmessungen
einschliesslich der zwei vom Owner entschiedenen rund 2 h 50 min.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der `occ`-Wrapper reichte `OC_PASS` an nichts weiter**

- **Found during:** Task 2, Block 3 und Block 4
- **Issue:** `99b-runden.sh` und `98-sprachfaelle.sh` riefen
  `OC_PASS="..." occ user:add --password-from-env`. Zwei Schichten fressen eine
  Umgebungsvariable auf dem Weg in den Container, und der Entwurf ueberquerte
  keine: `sudo` raeumt die Umgebung unter `env_reset`, und `docker exec` gibt
  von sich aus keine weiter. Die Antwort war
  `--password-from-env given, but NC_PASS/OC_PASS is empty!`. Fall 2 der
  Rundenzaehlung bekam nie ein Konto, und die Sprachfaelle endeten mit
  Rueckgabewert 15 aus dem falschen Grund.
- **Fix:** Der Wrapper ueberquert jetzt beide Schichten, mit
  `--preserve-env=OC_PASS` am `sudo` und `-e OC_PASS` am `docker exec`, und nur
  wenn die Variable ueberhaupt gesetzt ist. Der WERT wird nach wie vor an
  keiner Stelle zum Argument, was T-10-27 verlangt. Beide Dateien tragen den
  Grund im Kopf.
- **Files modified:** `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/99b-runden.sh`,
  `docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh`
- **Commit:** `0a9b538`

**2. [Rule 2 - fehlende Sorgfalt] Die Rohdatei der Kaltstart-Reproduktion trug
Nutzerinhalte**

- **Found during:** Die Nachmessung nach dem Owner-Entscheid
- **Issue:** Der Protokollteil von `95c-kaltstart-reproduktion-teil2.txt` nahm
  die Rohzeilen des Nextcloud-Protokolls auf. Die sind bis **15.129 Zeichen**
  lang und tragen Ausschnitte aus Nutzerdateien. Die Datei war 65 KB gross und
  haette T-10-41 verletzt, waere sie so committet worden.
- **Fix:** Der Protokollteil ist durch eine Auswertung ersetzt, die nur
  Zeitpunkt, Ebene, App, `reqId` und die auf 300 Zeichen gekuerzte Meldung
  fuehrt. Die Messzeilen sind unveraendert. Die Datei ist jetzt 7 KB gross. Eine
  Gegenprobe ueber alle 61 Rohdateien sucht nach Schluesseln, Token,
  Passwortzuweisungen, Basic-Auth in URLs und Zeilen ueber 2.000 Zeichen und
  findet nichts.
- **Files modified:** `docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/95c-kaltstart-reproduktion-teil2.txt`
- **Commit:** `8045852`

### Abweichungen in der Reihenfolge, mit ihrem Grund

Alle stehen auch in `skripte/00-ablauf.md`, Abschnitt 2b, weil diese Datei
beschreiben muss, was gelaufen ist.

1. **Die Bloecke liefen als 11, 12, 10 statt 10, 11, 12.** Die Sprachfaelle
   brauchen zwei Wartefristen von zusammen bis zu 46 Minuten, Seitenroute und
   Rundenzaehlung zusammen keine zehn. Der Kostendeckel lief, und eine
   Reihenfolge, die den teuersten Schritt zuerst faehrt, haette die beiden
   billigen an den Deckel gedraengt. Keine der drei haengt von einer anderen ab.
2. **Der OOM-Beweis wurde ein drittes Mal erhoben.** Zwischen der Ablesung des
   Waechters (13:05:11Z) und dem Beginn dieses Plans (13:48:08Z) lagen 43
   Minuten Containerleben. Eine Ablesung unmittelbar vor dem ersten Eingriff ist
   billiger als die Frage, was in diesen 43 Minuten geschah.
   `07-oom-beweis.txt` beginnt mit einer wortgleichen Kopie von
   `96-oom-beweis.txt` und haengt die neuen an.
3. **`98-sprachfaelle.sh` lief zweimal**, um Fallstrick 11 auszuschliessen.
   Beide Laeufe kommen auf dasselbe Ergebnis; der Erstlauf liegt unveraendert
   als `98-sprachfaelle-erstlauf.txt` daneben.
4. **Zwei Rohdateien tragen Namen, die kein Skript vergibt.** `00-ende.txt` und
   `48-vektorbestand.txt` sind Auswertungen, die der Plan verlangt und fuer die
   es kein Skript gibt; ihre Kopfzeile nennt, woraus sie gerechnet sind.
   `99b-runden-alltag.txt` und `99b-runden-drift.txt` sind unveraenderte
   Auszuege aus `99b-runden.txt`.
5. **Drei zusaetzliche Neustarts des Containers** in der Kaltstart-Reproduktion,
   ausdruecklich vom Owner erlaubt, nachdem der OOM-Beweis erhoben und
   committet war. `memory.max` ist nach jedem aus der cgroup zurueckgelesen
   worden und stand jedes Mal auf 2147483648 (T-10-46).

## Authentication Gates

Einer, und er ist im Checkpoint geloest worden: `aws_box.sh status` und `stop`
lesen `AWS_ACCESS_KEY_ID` und `AWS_SECRET_ACCESS_KEY` ausschliesslich aus der
Umgebung, und sie lagen nicht auf dieser Platte. Der Owner hat die Datei
`~/.findling-aws.env` genannt. Sie ist fuer den `status`-Aufruf in die Umgebung
geladen worden; weder ihr Inhalt noch ihr Pfad steht in einer Rohdatei oder in
einem Commit.

## Was dieser Plan offen laesst

- **Die Ursache der Mehrlaufzeit.** Die Kopplung der Spuren ist der Kandidat,
  den die Daten stuetzen: beide Spuren wurden gleichzeitig und um denselben
  Faktor langsamer, der Durchsatz war ueber 22 Stunden stabil bei 34 je Minute,
  und ein Nachlauf mit 170 Dokumenten je Minute kommt nicht vor. Die
  Zulauf-Luecken aus 10-05 erklaeren eine Wartezeit, aber nicht den
  Gleichschritt. Welcher traegt, entscheidet eine Messung, die dieser Plan
  nicht vorsieht.
- **Was `REQUEST_TIMEOUT_SECONDS` werden soll.** Dieser Plan liefert die Zahl
  (Containeraufruf reisst 1.501 ms beim ersten Start nach langer Pause), nicht
  die Entscheidung. Sie gehoert in Phase 11.
- **Was `MAX_ROUNDS` werden soll.** Dasselbe, und die Diagnose der Sprachfaelle
  ist das Argument dafuer, dass die Frage nicht theoretisch ist.
- **Warum das Lastwerkzeug einen abgebrochenen Containeraufruf als Erfolg
  zaehlt.** `search_load.py` sieht HTTP 200 und zaehlt. Ob es die Trefferzahl
  oder das Protokoll heranziehen soll, ist eine Entscheidung ueber das
  Werkzeug und gehoert nicht in einen Messlauf.
- **`aws_box.sh stop` und der Nachtrag der vier `box.env`-Schluessel.** Sie
  gehen auf Owner-Entscheid an Plan 10-07.
- **Die `CLAUDE.md`-Zeile "Tokenizer und Splitter, 544 MB".** Zugesagt, gehoert
  in Plan 10-07.

## Self-Check: PASSED

Alle 17 genannten Dateien existieren, alle fuenf Commits sind in `git log`
nachweisbar, 61 Rohdateien liegen unter `rohdaten/`. Die Gegenprobe auf
Geheimnisse, Token und Nutzerinhalte ueber alle 61 Dateien findet null
verdaechtige Stellen. `git diff` nennt keine Datei unter `php/` oder
`backend/src/` und `CLAUDE.md` ist unveraendert. Kein Em-Dash und kein En-Dash
in den neuen Dateien.
