# Die v1.2-Messanfahrt (Phase 15)

Diese Anfahrt liefert den Messbeleg des Milestones v1.2: MEM-02 (Rueckkehr zur
Grundlast nach einem Indexlauf), die Wirkung der Modell-Entladung (MEM-01,
Vorschlagswert 900 s, gemessen mit TTL 120 s), die Filter- und Sortiermessung
und die Sprachfaelle. Der Ablauf und die vorher aufgeschriebene Erwartung
stehen in `skripte/00-ablauf.md`, die Rohdaten in `rohdaten/`.

Anfahrt freigegeben: 2026-09-20, Deckel 46 h / 5,40 USD

Die Freigabe hat der Owner am Checkpoint 15-08 erteilt (siehe
`.planning/phases/15-messphase-eine-box-anfahrt/15-08-SUMMARY.md`), zusammen
mit den Antworten auf die drei Fragen: er setzt den A-Record
`loadtest.infranode.dev` selbst, der Korpus-Snapshot snap-03f1d1d9ad9262704
bleibt stehen (nur der Ende-Snapshot dieser Anfahrt faellt), und die
Entlade-Messung faehrt mit TTL 120 s. Der Abbau der Box ist nicht Teil dieser
Freigabe; er ist Plan 15-14 mit eigener Bestaetigung.

**Zur Schreibweise.** Die Abschnittsueberschriften stehen ohne Umlaute, weil
Pruefungen und Verweise auf sie zeigen. Der Fliesstext benutzt durchgehend echte
Umlaute. Adressen, Kennungen und Passwoerter der Box stehen in keiner Zeile
dieser Datei; die einzigen beiden Ausnahmen sind der oeffentliche Name
`loadtest.infranode.dev` und der Korpus-Snapshot snap-03f1d1d9ad9262704, die
beide bereits committet im Repositorium stehen.

---

## 1. Was dieser Lauf war

Dieser Lauf war eine bezahlte Anfahrt auf eine gemietete Maschine, vom
20.09.2026 um 01:38Z bis zum 21.09.2026 um 03:23Z, freigegeben mit Deckel und
Datum, danach vollstaendig abgebaut.

Er war zugleich der **Erstvollzug des Runbooks** `docs/runbook-messbox.md`: der
gesamte Weg vom Anlegen der Maschine ueber den Wiederaufbau aus dem
Korpus-Snapshot bis zum Abbau ist vor diesem Lauf nie als Kette gefahren worden,
sondern aus Skripten, Rohdaten frueherer Laeufe und lesenden Proben
zusammengetragen gewesen.

Und er hat die vier offenen Messauftraege des Milestones erhoben: den
Wirkungsbeleg der Top-up-Route (DI-10-04), die vier regressiven Laststufen, die
Sprachfaelle (DI-10-02 und DI-11-01) und die Wiederaufwaerm-Kosten der Entladung
samt MEM-02. Dazu den vom Owner bestellten Filter- und Sortierblock (D-01).

---

## 2. Die Bedingungen

Die sechs protokollpflichtigen Vergleichbarkeitsgroessen aus Abschnitt 6 des
Runbooks, mit ihren gelesenen Werten und ihrer Rohdatei:

| Groesse | Sollwert | Gelesener Wert | Rohdatei |
|---|---|---|---|
| Zeilenstaende der Zustandstabelle | 52.111 indexiert, 37 uebersprungen, 0 fehlgeschlagen | nicht mehr ablesbar, ersetzt durch den Korpusbeleg **52.114 Dokumente** (Owner-Entscheid am Tor, siehe unten). Endstand des Laufs: **52.137 / 44 / 6** | `04-bestand-vor-der-messung.txt`, `90-bestand.txt` |
| Cron-Intervall der Instanz | 300 s, Toleranz zehn Prozent | **300 s**, Quelle `aio-cron-container`, Modus `cron` | `97-cron-vorpruefung-vorher.txt` |
| Instanztyp und harte Containergrenze | m7g.large, 2147483648 in der cgroup | **m7g.large**, `memory.max` 2147483648, `memory.swap.max` **0** (die Erwartung des Runbooks war hier falsch, siehe Abschnitt 10) | `03-aufbau.txt`, `92b-wechsel.txt` |
| Zeit seit dem letzten Containerstart | kein Sollwert, abzulesen | Containerstart **2026-09-20T02:42:05Z**, Abstand zum Trigger des Volllaufs **1 h 07 min**; je Messblock eigene Zeile | `96b-waechter.txt`, `94b-...`, `95b-...`, `99c-...` |
| Werkzeugstand als Baumhash | kein Sollwert, `baumhash-gleich` abzulesen | **`baumhash-gleich ja`**, Baumhash `f3f1fb13...` ueber 54 Paketdateien, dreifach verankert und zusaetzlich im **laufenden** Container nachgelesen | `40b-baumhash.txt`, `92b-wechsel.txt` |
| Stellung des Entladeschalters | kein Sollwert, je Messblock abzulesen | siehe die Tabelle darunter | je Rohdatei eine Pflichtzeile |

**Der Abbilddigest.** Gezogen wurde per Digest und nicht ueber den wandernden
Zeiger `:dev`:

```
ABBILD_DIGEST sha256:80710fbba1a4acf6d60671ff60b0aeb85d902228338771e69fb62fe2a14bf706
abbild arch=arm64 created=2026-09-19T17:56:47Z
```

Der Digest ist die Notiz, der Baumhash der Beweis. Beide stehen in
`40b-baumhash.txt`.

**Die Maschine.** 3.9Gi Gesamtspeicher, 2 Kerne, aarch64, `mem=4G` in der
Kommandozeile des Kerns zurueckgelesen, Korpus-Volume 59G mit 35G belegt.

**Die Schalterstellung je Messblock.** Die Zeile `entladeschalter-ist` steht in
jeder Rohdatei; ohne sie gilt ein Block als unvollstaendig (Abschnitt 6.4 des
Runbooks):

| Messblock | `FINDLING_EMBED_IDLE_RELEASE_SECONDS` |
|---|---|
| Abbildwechsel, Zustandspruefung, Nullstand | 0 |
| Volllauf (Schritt 4) und Cron-Zweige | 0 |
| Laststufen (Schritt 6) | 0 |
| Filter und Sortierung (Schritt 6b) | 0 |
| Sprachfaelle (Schritt 7) | 0 |
| Wiederaufwaermen (Schritt 8), Auspraegungen 1 und 2 | **120** |
| Wiederaufwaermen (Schritt 8), Auspraegungen 3 und 4 | 0 |
| MEM-02 (Schritt 8b) | **120** |
| Endmessungen (Schritt 9) | 0 |

Die 120 s statt der 900 s des Vorschlagswerts sind der Owner-Entscheid D-02 vom
19.09.2026, bestaetigt als Frage C am Checkpoint 15-08. Gemessen wird damit
derselbe Mechanismus bei einem Bruchteil der Box-Zeit; die einzige
Einschraenkung ist, dass diese Messung ueber die **Haeufigkeit** von Entladungen
im Alltag nichts sagt.

**Die drei Protokollbloecke, woertlich.** Der Konfigurationszweig:

```
cron-modus-ist cron
cron-intervall-quelle aio-cron-container
cron-intervall-ist 300
```

Der Wirkungszweig (zur Herkunft dieser Zahlen siehe Abschnitt 4 und 10):

```
lauffenster 2026-09-20T03:49:32Z bis 2026-09-20T23:09:58Z (19 h 20 min)
ablesereihe-intervall 120
lesungen 578
vorrat-null-lesungen 15
vorrat-null-anteil 2,6 prozent
scheiben 23
scheibenabstand-min 120
scheibenabstand-median 301
scheibenabstand-max 361
wirkungsdeckel 420, ueberschreitungen 0
```

Die Bilanzzeile der Sprachfaelle, mit beiden Zahlen:

```
sprachfaelle bestanden 5 von 10, davon 5 nicht messbar
rote faelle 0, nicht messbare faelle 5, rote zusicherungen 0
```

**Der Owner-Entscheid am Abbruchtor.** Das Tor des Runbooks (Abschnitt 5) will
52.111 indexierte Dokumente sehen. Dieser Beleg war nicht mehr ablesbar, weil
der Abbildwechsel in Block 13b planmaessig mit `unregister --rm-data` das
Datenvolume des Backends geleert hatte. Vorgelegt wurde stattdessen der Korpus
selbst: 52.114 Dokumente unter dem Lastkonto, 20G Nutzdaten, konsistent mit den
52.111 der Snapshot-Beschreibung. Der Owner am 20.09.: **"Weiter, Korpus als
Beleg."** Der Widerspruch zwischen Tor und Abbildwechsel ist ein
Runbook-Befund und steht in Abschnitt 10.

---

## 3. Urteil je Erwartung, E1 bis E14

Die Erwartungen stehen seit dem 19.09.2026 committet in
`skripte/00-ablauf.md`, Abschnitt 3 und 3.1, also vor der ersten Box-Minute.
Sie sind fuer diesen Bericht **nicht** umformuliert worden; der Wortlaut unten
ist der Wortlaut dort. Erlaubt sind genau drei Urteile: `gehalten`, `verfehlt`,
`nicht entschieden`.

**Eine verfehlte Erwartung ist ein Ergebnis und kein Grund fuer eine zweite
Anfahrt.** Drei der vierzehn sind verfehlt, und sie bekommen ihren Satz und
keine Entschuldigung.

| Nr | Erwartung, im Wortlaut | Gemessen | Urteil |
|---|---|---|---|
| E1 | Der Bestand je Begriff liegt ueber 26, fuer mindestens die Begriffe, die im Lastkorpus haeufig vorkommen | haeufige Begriffe 33.226 bis 51.965; kein Begriff traegt die 26 | **gehalten** |
| E2 | Die Fensterbelegung saettigt bei 100 und wird fuer haeufige Begriffe genau 100 melden | `fenster_lex=100` und `fenster_sem=100` fuer alle fuenf haeufigen Begriffe | **gehalten** |
| E3 | Mindestens einer der vier am 10.09. roten Faelle ist jetzt messbar oder wird ausdruecklich als nicht messbar mit einer Rangangabe ausgewiesen | alle vier (Genehmigung, Frist, Vertrag, bescheid) tragen `ausserhalb` gegen die Schwelle 64 und heissen nicht messbar; zusaetzlich sind zwei zuvor gruene Faelle mit Rang 1 belegt | **gehalten** |
| E4 | Das protokollierte Cron-Intervall betraegt 300 Sekunden, und die Zeile `cron-intervall-ist` nennt die Quelle daneben | `cron-intervall-ist 300`, `cron-intervall-quelle aio-cron-container` | **gehalten** |
| E5 | Der gemessene Scheibenabstand liegt unter 420 Sekunden | Median 301 s, Maximum 361 s, null Ueberschreitungen | **gehalten** |
| E6 | Die Ablesereihe des Wirkungszweiges ist mit ihrem Intervall benannt, also 120 Sekunden in der Zeile `ablesereihe-intervall` | `ablesereihe-intervall 120`, Quelle `96-statusseite.jsonl`, 578 Lesungen | **gehalten** |
| E7 | Der Bericht sagt, WELCHE Reihe seine Protokollzahl liefert, statt beide Prozentzahlen nebeneinanderzustellen | dieser Bericht nennt genau eine Reihe (120 s, 578 Lesungen, 15 ohne Vorrat) und keine zweite | **gehalten** |
| E8 | Nach dem Wechsel meldet `40b-baumhash.sh` `baumhash-gleich ja`, und der aufgeloeste Digest steht als protokollierte Zeile daneben | `baumhash-gleich ja`, Digest `sha256:80710fbb...4bf706` protokolliert, Baumhash zusaetzlich im laufenden Container gelesen | **gehalten** |
| E9 | Die Laufzeit beider Spuren liegt unter 26 h 37 min | 19 h 20 min, als Untergrenze gekennzeichnet | **gehalten** |
| E10 | Die Stufen 1 und 4 halten das Gruppenbudget von 2.500 ms, die Stufe 8 haelt es mit kleinerer Reserve als 374,5 ms, und die Stufen 12 und 16 reissen es weiterhin | Stufe 1 480,5 ms, Stufe 4 1.006,8 ms, Stufe 8 1.992,0 ms (Reserve **508,0 ms**, also groesser statt kleiner), Stufen 12 und 16 reissen mit 2.950,6 und 4.091,1 ms | **verfehlt** |
| E11 | `newest` und `oldest` antworten auf dem Vollbestand nicht um mehr als den Faktor zwei langsamer als `relevance`, und drei geblaetterte Seiten melden die Seitenzahlen 1, 2, 3 ohne eine Datei-Kennung zweimal | Faktor 1,95 (341,3 ms gegen 175,2 und 174,7 ms Median), Seitenzahlen 1, 2, 3, keine doppelte Kennung | **gehalten** |
| E12 | Die erste Suche nach einer Entladung bleibt unter 1,5 s | kalt **1.996 ms** (gerissen), warm **1.418 ms** (gehalten) | **verfehlt** |
| E13 | Die Rueckkehr zur Grundlast nach einem Indexlauf liegt ueber 300 MB, und der Bodensatz, der nicht zurueckkommt, liegt bei rund 16 MB | Rueckkehr **377,5 MB** (haelt), Bodensatz **628,0 MB** gegen die erwarteten 16 MB | **verfehlt** |
| E14 | Belegt werden die Folgen einer Frist und nie die Frist selbst. Der Vorschlagswert bleibt bei 900 s, wenn beide Bedingungen halten: die Rueckkehr liegt ueber 300 MB (E13) und die erste Suche nach einer Entladung bleibt unter 1,5 s (E12) | die zweite Bedingung reisst im kalten Eckfall, also ist die E12-Verzweigung der Regel gefallen und nicht die Hauptzeile; der Owner ist ihr gefolgt | **gehalten** |

**Die drei verfehlten Erwartungen, je ein Satz.**

- **E10 ist in die guenstige Richtung verfehlt.** Die Stufe 8 sollte das Budget
  mit kleinerer Reserve als 374,5 ms halten; sie haelt es mit 508,0 ms, also mit
  mehr Luft als in v1.1. Die Erwartung war eine Verschlechterung, weil der
  Zaehler seit dem 10.09.2026 abgebrochene Aufrufe nicht mehr als beantwortet
  zaehlt und denselben Zustand damit strenger misst; eingetreten ist eine
  Verbesserung. Die Erwartung bleibt verfehlt und wird nicht umformuliert.
- **E12 ist im kalten Eckfall gerissen.** 1.996 ms gegen die Decke von 1,5 s.
  Die Marge war auf der Entwicklungsmaschine mit 1,37 bis 1,44 s schon bei der
  Abnahme der Phase 14 ausdruecklich als duenn benannt; auf der langsameren Box
  ist sie aufgezehrt. Im warmen Fall, also im Alltag einer laufenden Box, haelt
  sie mit 1.418 ms. Genau dieser Fall ist es, wegen dessen die Marge benannt
  wurde.
- **E13 ist in ihrer zweiten Haelfte verfehlt, und der Grund ist ein
  Namensfehler in der Erwartung selbst.** Die erste Haelfte haelt mit 377,5 MB
  ueber der Schwelle 300 MB, und das ist die Messgroesse von MEM-02. Die zweite
  Haelfte vergleicht zwei verschiedene Groessen unter einem Namen: die 16 MB
  stammen aus der Zielast ueber fuenf Zyklen des Vorprueflaufs (Zuwachs je
  Zyklus), die 628,0 MB der Box sind der absolute Rueckstand nach **einem**
  Zyklus, also Modulimporte und Laufzeitstrukturen, die nach der ersten
  Einbettung resident bleiben. Die Erwartung wird nicht nachtraeglich getrennt;
  getrennt wird die Berichterstattung, in Abschnitt 8.

---

## 4. Der DI-10-04-Wirkungsbeleg

**Die Laufzeit.** Der Volllauf beider Spuren lief vom 2026-09-20T03:49:32Z bis
zum 2026-09-20T23:09:58Z, also **19 h 20 min**, gegen die 26 h 37 min des
v1.1-Laufs und die 18 h 56 min von v1.0. Ergebnis: 52.137 Dokumente und 52.137
Vektoren, Arbeitsvorrat am Ende null, `runState idle`, kein OOM
(`memory.peak` 2.044.096.512 Byte unter der Grenze von 2.147.483.648,
`OOMKilled=false`, `RestartCount=0`).

**Die Laufzeit ist eine Untergrenze.** Beim Anstoss lagen bereits 4.696 Dateien
im Index, weil der Poller seit dem Abbildwechsel um 02:42Z gebaut hatte. Der
v1.1-Lauf startete vergleichbar mit 1.653 Dateien und ist aus demselben Grund
ebenfalls eine Untergrenze; die beiden Zahlen sind gleichartig verzerrt, aber
nicht gleich stark.

**Der Leerlaufanteil, mit seiner Ablesereihe.** Die Reihe ist
`96-statusseite.jsonl`, eine Aufnahme alle **120 Sekunden**, 578 Aufnahmen im
Lauffenster. Davon zeigten **15** einen leeren Arbeitsvorrat, also **2,6
Prozent**, hochgerechnet **0,50 h** der 19 h 20 min. Der v1.1-Vergleichswert
sind 5,85 h von 26,6 h, also 22,0 Prozent. Es gibt in diesem Bericht keine
zweite Prozentzahl fuer denselben Sachverhalt, und das ist die Lehre aus v1.1,
wo 194 von 812 Lesungen gegen 62 von 325 Lesungen standen.

**Hat die Top-up-Route gewirkt? Die Zahlen entscheiden es nicht.** Sie zeigen
einen Lauf, der 7 h 17 min kuerzer ist und dessen Leerlaufanteil von 22,0 auf
2,6 Prozent gefallen ist. Aber die Instanz ist aus einem Snapshot neu aufgebaut
worden, das Abbild ist gewechselt, und seit v1.1 ist nicht nur die Top-up-Route
dazugekommen, sondern auch alles uebrige der Phasen 13 und 14. Beide
Erklaerungen bleiben moeglich: die Route wirkt, oder die neu aufgebaute Instanz
taktet ihren Zulauf anders. Der Satz stand vor dem Lauf in `00-ablauf.md` und
steht hier unveraendert.

**Was sich rechnerisch trennen laesst, und was nicht.** Die 5,35 h weniger
Leerlauf erklaeren rund drei Viertel der 7,17 h Zeitgewinn; das restliche
Viertel liegt im Durchsatz selbst und hat mindestens zwei Kandidaten (das neue
Abbild, der um 3.043 Dateien hoehere Startpunkt). Eine Zuordnung dieses Viertels
waere eine Schaetzung, und sie wird hier nicht vorgenommen.

---

## 5. Die vier regressiven Laststufen

Gemessen am 21.09.2026 zwischen 02:10:22Z und 02:13:52Z, fuenf Stufen, zehn
Runden je Stufe, 20 s Pause. `scripts/ops/search_load.py` ist nicht angefasst
worden (`git status --porcelain` leer), weil jede Aenderung daran die
Stufenzahlen gegen v1.1 unvergleichbar machte.

| Stufe | p95 v1.2 | p95 v1.1 | p95 v1.0 | Trefferdichte v1.2 (v1.1) | Verdikt |
|---|---|---|---|---|---|
| 1 | 480,5 ms | 464,3 ms | 481,6 ms | 5,40 (5,40) | nicht regressiv |
| 4 | 1.006,8 ms | 1.068,0 ms | 1.009,4 ms | 5,40 (5,40) | **behoben** |
| 8 | 1.992,0 ms | 2.125,5 ms | 1.915,0 ms | 5,25 (rund 5,0) | **behoben** |
| 12 | 2.950,6 ms | 3.453,4 ms | 3.045,4 ms | 5,40 | **behoben** |
| 16 | 4.091,1 ms | 4.446,2 ms | 3.782,7 ms | 5,21 (4,16) | **behoben** |

Die vier Verdikte sind wortgleich mit denen in `97-nebenlaeufigkeit.txt`:

- **Stufe 4 behoben:** p95 1.006,8 ms unterschreitet die v1.1-Zahl 1.068,0 ms,
  die Trefferdichte 5,40 ist gehalten.
- **Stufe 8 behoben:** p95 1.992,0 ms unterschreitet v1.1 (2.125,5 ms); die
  +4,0 Prozent des Werkzeug-Hinweises beziehen sich auf v1.0 (1.915,0 ms) und
  liegen im Rauschband. Trefferdichte 5,25 gehalten.
- **Stufe 12 behoben:** p95 2.950,6 ms unterschreitet sowohl v1.1 (3.453,4 ms)
  als auch v1.0 (3.045,4 ms). Trefferdichte 5,40.
- **Stufe 16 behoben:** p95 4.091,1 ms unterschreitet v1.1 (4.446,2 ms); die
  +8,2 Prozent des Werkzeug-Hinweises sind gegen v1.0 (3.782,7 ms). Die
  Trefferdichte 5,21 liegt ueber der v1.1-Dichte 4,16, ist also nicht gefallen.

**Die Gegenrechnung aus dem Nextcloud-Protokoll.** Gezaehlt wurde auf
`cURL error 28` im Protokoll der Nextcloud, unabhaengig vom Lastwerkzeug: im
Lastfenster 02:10 bis 02:13 **null** Treffer. Zwei Treffer um 02:0x stammen aus
dem Neustart der Kaltstartmessung, 72 weitere aus dem Snapshot der alten Box
(05.09. bis 10.09.) und gehoeren nicht zu dieser Anfahrt. Damit ist die
Ausfallzaehlung des Werkzeugs bestaetigt: alle als `failures` gemeldeten Faelle
sind echte Leertreffer (`EmptyResultGroup`, `min_hits=1` nicht erreicht) und
keine verschluckten Zeitueberschreitungen. Genau das war in v1.1 anders, wo das
Protokoll 17 Zeitueberschreitungen fuehrte, waehrend das Werkzeug `failures: 0`
meldete.

**Das Budget.** Die Stufen 12 und 16 ueberschreiten das 2.500-ms-Budget je
Einzelanfrage, wie in v1.0 und v1.1 auch. Das ist eine Eigenschaft hoher
Nebenlaeufigkeit auf zwei Kernen und kein Regressionsbefund.

**Die Vergleichbarkeit, ehrlich.** Diese Reihe laeuft gegen einen anderen
Vektorbestand und ein anderes Abbild als v1.1. Die p95-Zahlen sind gegen v1.1
gefuehrt, weil diese Phase gegen v1.1 misst; die v1.0-Spalte steht als zweite
Referenz daneben und nicht als Alternative.

---

## 6. Die Sprachfaelle

Gefahren am 21.09.2026 von 02:18:54Z bis 02:25:23Z, zehn Faelle, dreiwertig am
Rang der eigenen Datei gegen die Schwelle 64 (`MAX_RECHECKS_ABSOLUTE`).

Die Bilanzzeile mit ihren beiden Zahlen:

```
sprachfaelle bestanden 5 von 10, davon 5 nicht messbar
```

`ci-beleg: integration.yml Lauf 35471225104`. Dieser Lauf faehrt dieselben zehn
Faelle auf einer frischen Instanz **ohne** Fremdbestand, auf amd64, gegen den
PHP-Entwicklungsserver. Er ist die Haelfte der Aussage, die diese Box nicht
machen kann.

**Die Raenge der vier am 10.09.2026 roten Faelle:**

| Fall | Begriff | Urteil 10.09.2026 | Rang jetzt | Urteil jetzt |
|---|---|---|---|---|
| 1 | Genehmigung | ROT | ausserhalb (Bestand 51.965) | nicht messbar |
| 2 | Frist | ROT | ausserhalb (Bestand 51.956) | nicht messbar |
| 4 | Vertrag | ROT | ausserhalb (Bestand 51.111) | nicht messbar |
| 6 | bescheid | ROT | ausserhalb (Bestand 51.167) | nicht messbar |

**Nicht messbar ist kein Sprachbefund.** Die eigene Datei dieser vier Faelle
steht in beiden Ranglisten ausserhalb der 64 Rechecks, und keine Fusion bringt
sie von dort in Reichweite: RRF ordnet nach der Summe der Kehrwerte der Raenge,
und jedes Dokument, das in beiden Listen vor ihr liegt, liegt mit beiden
Summanden vor ihr. Die Ursache ist die Verduennung durch 52.111 Fremddokumente,
die dieselben Woerter tragen, und nicht die Sprachkette. Der Fremdbestand trennt
die Berechtigung und nicht den Index.

Die fuenf gruenen Faelle (Mueller, "drei Monate", Belehrung, Auszug,
Erinnerung) stehen je auf Rang 1. Null rote Faelle, null rote Zusicherungen.
Der fuenfte nicht messbare ist Fall 7 (`type:pdf bescheid`, Bestand 33.226).

**Was das gegen den 10.09. ist.** Damals hiess die Bilanz `6 von 10, davon 0
nicht messbar`, und vier Faelle waren rot, weil die Messgroesse an einem Deckel
von 26 haengte, den keine Tiefe und kein Begriff bewegte. Der Deckel ist weg:
Abschnitt 0 des Laufs misst den Bestand im Prozess des Containers, und kein
Begriff traegt mehr die 26.

---

## 7. Filter und Sortierung, eine Erstmessung

Gefahren am 21.09.2026 von 02:17:56Z bis 02:18:07Z gegen den Vollbestand von
52.137 Vektoren, ueber die Seitenroute (nur sie traegt `types` und `sort`,
Befund 13-12), Anmeldung ueber Sitzung, Begriff "Bescheid Antrag",
Filter-Typgruppe `pdf`, fuenf Runden je Zeile.

**Dies ist eine Erstmessung.** Es gibt keinen v1.1-Wert fuer Sortierung oder
Blaettern unter Filter, weil beide erst in Phase 13 entstanden sind. Keine Zahl
dieses Abschnitts darf neben eine Vergleichszeile geraten.

| Modus | Median | p95 | Treffer |
|---|---|---|---|
| relevance | 341,3 ms | 449,0 ms | 25 |
| newest | 175,2 ms | 220,3 ms | 25 |
| oldest | 174,7 ms | 235,6 ms | 25 |

Der Faktor relevance zu newest und oldest liegt bei **1,95**, also unter dem in
E11 erwarteten Faktor zwei. Der Grund steht in der Rohdatei: unter `newest` und
`oldest` gibt es keine Fusion, der Zweig ist rein lexikalisch, jeder Treffer
traegt `score = 0.0`. Die drei Zahlen sind untereinander vergleichbar; gegen
`relevance` nur bedingt, weil `relevance` die Fusion beider Listen
einschliesst.

**Das Blaettern unter Filter.** Seite 1 wird gebaut, jede weitere wird aus dem
Weiter-Link **gezogen**, weil eine selbstgebaute Adresse ohne Fingerabdruck den
stillen Rueckfall auf Seite 1 messen wuerde (13-08).

| Seite | Antwortzeit | Treffer | Gemeldete Seitenzahl | Doppelte Kennungen |
|---|---|---|---|---|
| 1 | 332,7 ms | 25 | 1 | keine |
| 2 | 332,1 ms | 25 | 2 | keine |
| 3 | 333,2 ms | 25 | 3 | keine |

Der Cursor haelt ueber drei Seiten, die Antwortzeit ist ueber alle drei Seiten
flach.

**Die zweite Haelfte ist bewusst nicht gefahren.** Der Anmeldeweg Basic Auth
wurde ausgelassen, um Box-Zeit zu sparen; er kostet auf der Vergleichsinstanz
0,318 s je Anfrage (Befund M-03), die kein angemeldeter Nutzer zahlt, und zwei
Berichte sind nur ueber denselben Anmeldeweg vergleichbar. Die Auslassung steht
als Protokollzeile in der Rohdatei und nicht nur hier.

---

## 8. Wiederaufwaerm-Kosten und MEM-02

### 8.1 Die vier Auspraegungen

Gefahren am 21.09.2026 von 02:47:32Z bis 02:54:34Z, in der Reihenfolge 1, 3, 2,
4 (kalt vor warm), belegt durch die Containerstart-Zeitstempel der vier
Rohdateien. Jede Kaltmessung beginnt mit einem Containerneustart und einem
geleerten Seitencache des Wirts.

| Auspraegung | Schalter | Seitencache | erste Suche | Treffer | zweite Suche |
|---|---|---|---|---|---|
| 1 | 120 s | kalt | **1.996 ms** | 26 | 1.038 ms |
| 2 | 120 s | warm | **1.418 ms** | 26 | 745 ms |
| 3 | 0 | kalt | 2.051 ms | transient 0 | 776 ms |
| 4 | 0 | warm | 1.613 ms | 26 | 743 ms |

**Die Entladung kostet nicht mehr als ein normaler Kaltstart.** Im selben
Cachezustand liegt die Auspraegung mit Entladung je unter der ohne: 1.996 gegen
2.051 ms kalt, 1.418 gegen 1.613 ms warm. Die erste Suche der Nutzerroute traegt
die Volltextseite, waehrend die Gewichte im Hintergrund nachladen
(`nachwaermdauer-s=0`).

**Was die kalte Zahl mit enthaelt.** Das Leeren des Wirtscaches verwirft auch
den mmap-Cache des Tantivy-Index. Die kalten Zahlen messen damit **beide
Haelften kalt**, die Semantik und den Volltext, und nicht allein das Nachladen
der Gewichte. Das ist die gewollte schlechtere Haelfte der Wahrheit: sie ist der
Fall, den ein Nutzer nach einem Neustart der Box wirklich bekommt. Ohne diesen
Satz laese sich eine Zahl als Wiederaufwaermkosten, die zum Teil Indexkosten
sind.

Die null Treffer der Auspraegung 3 sind ein voruebergehender Leertreffer
unmittelbar nach dem Containerneustart (der mmap war noch kalt); die zweite
Suche derselben Auspraegung liefert regulaer, und die Latenz 2.051 ms bleibt als
Kaltstart-Bezugswert gueltig, weil der Lade- und mmap-Weg unabhaengig von der
Trefferzahl durchlaufen wird.

### 8.2 MEM-02, die Rueckkehr zur Grundlast

Gefahren am 21.09.2026 von 03:06:32Z bis 03:09:46Z, Schalter auf 120 s,
gerechnet ueber `anon` aus `memory.stat` und nicht ueber `memory.current`.

| Marke | Was sie ist | Wert |
|---|---|---|
| A | Grundlast vor dem Indexlauf, nach Containerneustart, Zustand `cold` | 103,9 MB |
| B | unmittelbar nach dem Indexlauf, Zustand `loaded` | 1.109,4 MB |
| C | nach der Ruhezeit, Zustand `unloaded` | 731,9 MB |

**`rueckkehr-zur-grundlast-mb = 377,5`**, gerechnet als Marke B minus Marke C,
also ueber der Schwelle von 300 MB aus E13. Bezugszahl ist ausdruecklich Marke
B und nicht Marke A: gefragt ist, ob die Speicherhalter nach Ablauf der Frist
wieder frei sind, und nicht, um wie viel eine Zahl gefallen ist.

Der Indexlauf ist ueber den Weg eines Nutzers angestossen worden (zwoelf kleine
Textdateien ueber WebDAV plus `files:scan`) und nicht ueber
`findling:index --restart`, das rund 52.000 Dokumente neu in die Schlange
gestellt haette; der Container waere dann nie in den Leerlauf gefallen. Belegt
ist er an den eingebetteten Dokumenten der Statusseite: 52.137 vorher, 52.149
nachher, Arbeitsvorrat je null. Der Korpus des Indexlaufs ist nach der letzten
Marke wieder entfernt worden.

**Der Bodensatz ist eine eigene Zahl und gehoert dem Owner vorgelegt.**
`bodensatz-mb = 628,0` (Marke C minus Marke A). Die 16 MB der Erwartung E13
stammen aus der Zielast ueber fuenf Zyklen des Vorprueflaufs, sind also ein
Zuwachs je Zyklus; die 628,0 MB sind der absolute Rueckstand nach **einem**
Zyklus. Zwei verschiedene Messgroessen unter einem Namen, und deshalb ist E13 in
Abschnitt 3 verfehlt. Die Zahl, die zaehlt, ist diese: **ein Container, der
einmal eingebettet hat und danach entladen ist, steht auf 731,9 MB residentem
Speicher.** Auf einer 4-GB-Box ist das eine Zahl, die man kennt.

### 8.3 Der Owner-Entscheid zum Vorschlagswert 900 s, im Wortlaut

Vorgelegt wurde E14 in der seit dem 19.09.2026 committeten Fassung, also mit
einem Zeitstempel vor den Rohdaten. E13 haelt (Rueckkehr ueber 300 MB), E12
reisst im kalten Fall und haelt im warmen.

> **Owner-Entscheid: "900 s bleibt + Vorbehalt (E14-Regel)."**

Der Vorschlagswert bleibt damit eine gekennzeichnete Schaetzung. Seine
Beschreibung bekommt die Box-Zahlen daneben (kalt 1.996 ms, warm 1.418 ms) und
den Satz, dass die 1,5-s-Decke nur im kalten Eckfall nach einem Box-Neustart
reisst und im laufenden Betrieb haelt. Korrigiert wird der Wert nicht, genau wie
E14 es fuer den E12-Riss vorschreibt: eine Frist laesst sich nicht belegen, nur
ihre Folgen, und eine Empfehlung bleibt eine Empfehlung.

---

## 9. Kosten

| Groesse | Wert |
|---|---|
| Laufzeit der Box | **25,75 h** (2026-09-20T01:38Z bis 2026-09-21T03:23:57Z) |
| Kosten | **2,9831 USD netto** |
| Freigegebener Deckel (15-08, Owner, 20.09.2026) | **46 h / 5,40 USD netto** |
| Differenz | **20,25 h / 2,42 USD unter dem Deckel** |

**Der Deckel hat gehalten: ja.** Auch die ausgewiesene Untergrenze des
Rechenblatts (31 h / 3,59 USD, der v1.1-Verbrauch bei kleinerem Umfang) ist
unterschritten, weil der Volllauf mit 19 h 20 min schneller war als die 26 h
37 min von v1.1 und die Messbloecke danach zuegig liefen. Die Kostenhistorie
ist **vor** dem Abbau committet worden (Commit df1d11c belegt die Reihenfolge),
weil `aws_box.sh destroy` die Zustandsdatei loescht.

Laufende Kosten nach dem Abbau: der Korpus-Snapshot snap-03f1d1d9ad9262704 mit
2,79 bis 2,99 USD je Monat, gewollt und vom Owner zweimal bestaetigt. Sonst
nichts.

---

## 10. Was dieser Lauf nicht besser gemacht hat

Dieser Abschnitt ist Pflicht und nicht Zugabe.

1. **Der Wirkungszweig des Cron-Checks ist nie live gelaufen.** Beim Anstoss des
   Volllaufs ist `./97-cron-vorpruefung.sh waehrend` schlicht nicht gestartet
   worden, und es ist erst nach dem Ende des Laufs aufgefallen. Die Zahlen des
   Wirkungszweiges sind deshalb **nachtraeglich** aus der aufgezeichneten
   120-s-Statusreihe berechnet und in der Rohdatei ausdruecklich so
   gekennzeichnet. Der Live-Zweig haette mit seinem eigenen Intervall anders
   gezaehlt. Das Urteil zu E5 und E6 traegt diesen Vorbehalt mit.
2. **Die Wirkung der Top-up-Route ist nicht entschieden.** Siehe Abschnitt 4:
   die Instanz ist neu aufgebaut, das Abbild gewechselt, und beide Erklaerungen
   des Zeitgewinns bleiben moeglich. DI-10-04 ist gemessen und nicht geklaert.
3. **Die Zeilenstaende des Abbruchtors sind nicht abgelesen worden.** Das Tor
   will 52.111 / 37 / 0 sehen; der Abbildwechsel in Block 13b hat das
   Datenvolume vorher planmaessig geleert. Der Owner hat den Korpus als Beleg
   genommen. Das ist ein Widerspruch im Runbook und kein Messwert: Abschnitt 5
   und 6 des Runbooks stammen aus dem Ablauf ohne Abbildwechsel. Nachgetragen
   in `docs/runbook-messbox.md`.
4. **Die Endzahlen 52.137 / 44 / 6 sind eine Erstmessung.** Gegen die 52.111 /
   37 / 0 der Phase 10 gemessen, aber gegen ein anderes Abbild; die sechs
   fehlgeschlagenen und die 44 uebersprungenen Dateien sind nicht untersucht
   worden. Wer sie erklaeren will, braucht einen Lauf, der sie einzeln
   benennt.
5. **Filter und Sortierung stehen ohne Vergleichszeile da.** Abschnitt 7 ist
   eine Erstmessung. Es gibt nichts, wogegen die 341,3 ms sich verbessert oder
   verschlechtert haben koennten.
6. **Die Kaltstartlatenz aus DI-07-02 ist nicht sauber ablesbar.** Der
   Einzelrequest der Kaltstartmessung traf einen Leerbegriff
   (`EmptyResultGroup`); die anon-Spitze 526,4 MB und die rund 2 s Wandzeit
   stehen, die Latenzaussage steht nicht.
7. **Der Bodensatz von 628,0 MB ist eine benannte Zahl ohne Vergleich.** Siehe
   Abschnitt 8.2. Ob er sich durch eine zweite Entladung weiter senkt, misst
   dieser Lauf nicht: gefahren wurde genau ein Zyklus.
8. **Drei Werkzeuge sind waehrend der bezahlten Zeit geaendert worden**, je mit
   ausdruecklichem Owner-Wort und je mit boxlosen Tests nachgezogen: zweimal
   `92b-wechsel.sh` (die Erwartung 2147483648 im Swap-Feld war falsch, und der
   Vergleich zweier Kennungsarten las den richtigen Inhalt als fremd) und einmal
   `97-cron-vorpruefung.sh` (der Intervall-Leser las 5 s statt 300 s). Das
   Runbook verbietet in Abschnitt 7.1 genau das. Die drei Aenderungen sind
   Ausnahmen mit Begruendung und keine neue Praxis; die Zahlen daneben stammen
   je aus dem Lauf **nach** dem Fix.
9. **Zwei Werkzeug-Befunde sind offen geblieben.** Die Phase-B-Pipeline von
   `92b-wechsel.sh` verschluckt Fehler des `occ`-Aufrufs (Lauf 1 endete mit
   Rueckgabewert 0, ohne dass die Registrierung stattgefunden hatte), und
   `99c-filter-sortierung.sh` liest das Passwort nicht aus der Passwortdatei,
   sondern erwartet es in der Umgebung. Beide gehoeren in die Zeit nach dem
   Abbau und sind hier nur benannt.
10. **Die fuenf offenen Fragen der Phasenrecherche, soweit sie offen geblieben
    sind.** Vier sind entschieden und vollzogen: das gemessene Abbild (Q1, per
    Digest gewechselt), das Belegkriterium des Vorschlagswerts (Q2, als E14
    vorher festgeschrieben und in 15-13 entschieden), der Filter- und
    Sortierblock (Q3, gefahren als Schritt 6b) und die Ausfuehrungsform (Q4,
    begleitete Sitzung). Offen bleibt **Q5, die Wiedervorlage des
    Korpus-Snapshots**: snap-03f1d1d9ad9262704 steht mit 2,79 bis 2,99 USD je
    Monat weiter, der Owner hat ihn zweimal bewusst behalten, und die
    Entscheidung ueber Loeschen oder eine guenstigere Speicherklasse ist nach
    v1.2 faellig. Diese Zeile ist die Wiedervorlage.
11. **Kein Werkzeug-Fix dieser Anfahrt ist in seiner Wirkung nachgemessen
    worden.** Die drei Fixes aus Punkt 8 sind gegen boxlose Tests gruen; ob sie
    auf einer Box das tun, was sie sollen, sagt erst die naechste Anfahrt.

---

## 11. Die Rohdateien dieses Laufs

Alle Rohdaten liegen in `rohdaten/`, alle Werkzeuge in `skripte/`. Die sechs in
dieser Anfahrt gefahrenen Messfassungen tragen seit Plan 15-15 einen
Pruefsummen-Waechter in `backend/tests/test_measurement_scripts.py`: eine
gefahrene Messfassung ist Teil des Belegs und wird danach nicht mehr angefasst.

| Rohdatei | Was darin steht |
|---|---|
| `01-aws-lesende-proben.txt` | die lesenden Proben vor der Anfahrt, Snapshot und Tags |
| `02-vorbedingungen.txt` | die neun Vorbedingungen ohne Box-Zeit, mit ihren Ausgaben |
| `03-aufbau.txt` | die Bloecke 1 bis 13b des Erstvollzugs, mit acht Abweichungen |
| `04-bestand-vor-der-messung.txt` | die Zustandspruefung und das Owner-Tor |
| `05-sprachfaelle.txt` | Bestandssonde, zehn Faelle, Bilanzzeile, `ci-beleg` |
| `07-snapshot-und-abbau.txt` | Verbleib des Korpus-Snapshots und der Abbau |
| `40b-baumhash.txt`, `92b-wechsel.txt`, `92b-info-box.xml` | der Abbildwechsel und sein Beweis |
| `90-bestand.txt`, `96-vektorbestand.txt` | die Endmessungen vor dem Abbau |
| `93-nullstand.txt`, `93-kosten-und-verbleib.txt` | Nullstandsbeleg und Kostenhistorie |
| `94b-grundlast-rueckkehr.txt` | MEM-02, die drei Marken und die Rueckkehrzahl |
| `95-spitze-nachher.txt`, `95-nachher*.json`, `95-nachher.csv` | Kaltstart und Spitzenwerte |
| `95b-wiederaufwaermen-1..4.txt`, `95b-gegenueberstellung.txt` | die vier Auspraegungen |
| `96-volllauf.csv`, `96-volllauf-start.txt`, `96-statusseite.jsonl`, `96b-waechter.txt`, `96-oom-beweis.txt` | der Volllauf und seine Beobachter |
| `97-cron-vorpruefung-vorher.txt`, `97-cron-vorpruefung-waehrend.txt` | die beiden Cron-Zweige |
| `97-nebenlaeufigkeit.txt`, `97-nebenlaeufigkeit.csv`, `97-stufe-*.json` | die fuenf Laststufen |
| `99c-filter-sortierung.txt` | Sortierung und Blaettern unter Filter |
| `00-FERTIG` | die Fertigmeldung des Volllaufs |
