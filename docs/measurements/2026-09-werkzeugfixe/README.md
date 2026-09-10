# Die Werkzeug-Anfahrt vom 10.09.2026

Diese Anfahrt beweist zwei Werkzeug-Fixe gegen den echten Lastkorpus und sonst
nichts. Der Ablauf und die vorher aufgeschriebene Erwartung stehen in
`skripte/00-ablauf.md`, die Rohdaten in `rohdaten/`.

Anfahrt freigegeben: 2026-09-10, Deckel 4 h / 0,50 USD (D-01)

Der Abbau der Box ist nicht Teil dieser Freigabe. Er ist Plan 11-12 mit eigener
Bestätigung (D-03).

**Das Ergebnis in zwei Sätzen.** DI-10-01 ist geschlossen: der neue Zähler des
Lastwerkzeugs findet die Abbrüche, die die alte Fassung übersah, und seine Zahl
lässt sich Anfrage für Anfrage gegen das Nextcloud-Protokoll aufrechnen.
DI-10-02 ist **nicht** geschlossen: die Vorprüfung des Fremdbestands misst auf
dieser Instanz einen Deckel der Antwort und nicht den Bestand dahinter, und
deshalb urteilt das Sprachfall-Skript wieder zweiwertig.

---

## 1. Was gefahren wurde

| Posten | Zahl | Rohdatei |
|---|---|---|
| Anfahrt | 2026-09-10T21:51:06Z bis 23:49:11Z | `rohdaten/06-kosten.txt` |
| Laufzeit | 1,97 h von 4,00 h freigegeben | `rohdaten/06-kosten.txt` |
| Kosten | 0,2285 USD von 0,50 USD freigegeben | `rohdaten/06-kosten.txt` |
| Maschine | `aarch64`, 2 Kerne, `mem=4G` im Kern | `rohdaten/04-bestand-vor-der-messung.txt` |
| Harte Grenze des Containers | 2.147.483.648 aus der cgroup | `rohdaten/04-bestand-vor-der-messung.txt` |
| Nextcloud-Instanzen am Docker-Dienst | 1, wie D-02 verlangt | `rohdaten/04-bestand-vor-der-messung.txt` |
| Messblock A | 160 plus 80 Anfragen, rund 15 Minuten | `rohdaten/01-lastwerkzeug-stufe16.json`, `rohdaten/02-lastwerkzeug-stufe08.json` |
| Messblock B | zehn Fälle, `FRIST=60 RUNDEN=10` | `rohdaten/05-sprachfaelle.txt` |

Drei Fallen der Anfahrtsliste haben zugeschlagen, alle drei bekannt und alle
drei vorher aufgeschrieben. Der Pin in `/etc/hosts` zeigte auf 172.18.0.9,
während der Apache-Container auf 172.18.0.4 lag; er wurde nachgezogen. Der
Container war nach dem Maschinenstart nicht von AppAPI gestartet, also lief die
DI-05-36-Heilung. Die Adresse der Box wechselte auf 3.75.242.128, und
`aws_box.sh start` zog die SSH-Regel selbst nach.

## 2. Der Bestand, und warum er nicht die erwartete Zahl trug

Die Abbruchbedingung der Freigabe lautete 52.111 indexiert, 37 übersprungen,
0 fehlgeschlagen. Gemessen wurden **52.137 / 44 / 6**. Die Anfahrt hielt an
dieser Stelle an, der Ist-Stand ging nach
`rohdaten/04-bestand-vor-der-messung.txt`, und der Owner entschied neu.

Die Differenz ist aufgeklärt und nicht geglättet: sie beträgt genau 39 und
gehört dem Konto `sprachfall`, also dem Referenzkorpus, den der Lauf vom 10.09.
**nach** der Vergleichsmessung hochgeladen hat. Die sechs fehlgeschlagenen
Dateien sind die sechs absichtlich kaputten Dateien dieses Korpus
(`corpus/06-zero-bytes.pdf` und fünf weitere, mit Grund `empty_file` und
`corrupt`). Der Lastkorpus selbst steht unverändert bei 49.980 indexiert und
20 übersprungen. Der Owner hat die Fortsetzung am 10.09. freigegeben.

Zwei Dinge sind dabei aufgefallen und gehören in den nächsten Plan, der diese
Bedingung schreibt. Erstens taugt `occ findling:index --status` für diese
Prüfung nicht: es meldet `indexed` bauartbedingt immer als 0, die Zahl kommt aus
der Container-Zählung. Zweitens widerspricht die Zahl 52.111/37/0 der Annahme
A5 desselben Plans, nach der die 39 Dateien auf der Box liegen sollen. Beide
Bedingungen können nicht gleichzeitig gelten.

## 3. DI-10-01, geschlossen

**Der Befund.** `search_load.py` zählte eine Ergebnisgruppe ohne Containerteil
als Erfolg. Die Rohdatei des 10.09. meldet `"failures": 0` über 160 Anfragen,
während das Nextcloud-Protokoll im selben Fenster 17 Abbrüche trägt.

**Die beiden Zählungen dieses Laufs, nebeneinander.**

| Stufe | Werkzeug: `failure_kinds["EmptyResultGroup"]` | Protokoll: `cURL error 28` | Begriff ohne Treffer | Summe der beiden Ursachen |
|---|---|---|---|---|
| 16 | **30** | **14** Vorgänge (28 Zeilen) | 16 | 16 plus 14 gleich **30** |
| 8 | **9** | **0** Vorgänge | 8 | 8 plus 0 gleich **8** |
| 1 (Gegenprobe) | **1** | **0** Vorgänge | 1 | 1 plus 0 gleich **1** |

Rohdateien: `rohdaten/01-lastwerkzeug-stufe16.json`,
`rohdaten/02-lastwerkzeug-stufe08.json`, `rohdaten/03-nc-protokoll-abbrueche.txt`.

**Die Lücke ist gemessen und nicht vermutet.** Der neue Zähler meldet auf
Stufe 16 dreißig Fehlschläge, das Protokoll vierzehn Abbrüche. Beide Zahlen sind
richtig, weil sie zwei verschiedene Ursachen derselben Erscheinung zählen. Der
Begriff **Mahnung** trägt im Lastkorpus keinen einzigen Treffer, gemessen ohne
Last in 486 Millisekunden; er fällt unter `--min-hits 1` und wird als
`EmptyResultGroup` gezählt, obwohl nichts abgebrochen ist. Die Begriffe
rotieren, also kommt er auf Stufe 16 genau 16 mal an die Reihe, auf Stufe 8 acht
mal, bei Nebenläufigkeit 1 einmal. Damit gehen zwei der drei Stufen exakt auf.

**Eine Zählung der Zeilen wäre eine doppelte gewesen.** Ein abgebrochener Aufruf
hinterlässt zwei Protokollzeilen, eine von `app_api` mit dem cURL-Text und eine
von `findling`, die ihn weiterreicht. Gezählt wurde deshalb nach `reqId`, also
nach Vorgang, und beide Zeilenzahlen stehen zur Kontrolle in der Rohdatei.

**Was offen bleibt.** Auf Stufe 8 bleibt eine Anfrage übrig: neun Fehlschläge
gegen acht erklärte. Das Protokoll trägt im Fenster der Stufe 8 und eine Minute
darüber hinaus keine einzige Zeile der Apps `findling` oder `app_api`. Diese
eine Anfrage bekam also eine leere Ergebnisgruppe, ohne dass irgendwo ein
Abbruch entstand. Als Vermutung beschriftet und nicht als Befund: das ist
DI-07-03, die Kandidatenschleife holt keine zweite Runde nach.

**Die Treffer je Anfrage, gegen den 10.09.**

| Stufe | 10.09.2026 | dieser Lauf | Rohdatei |
|---|---|---|---|
| 8 | 5,25 | **5,33** | `rohdaten/02-lastwerkzeug-stufe08.json` |
| 16 | 4,16 | **4,88** | `rohdaten/01-lastwerkzeug-stufe16.json` |

Erwartung E2 ist eingetreten, aber schwächer als am 10.09.: der Abstand
zwischen den Stufen beträgt 0,45 statt 1,09. Die Zahl, die der Leser früher von
Hand ausrechnen musste, steht jetzt im Bericht, und das war der Zweck des Fixes.

**Die Erwartungen aus `skripte/00-ablauf.md`, ohne Nachbesserung.**

| Nr | Erwartung | Eingetreten? |
|---|---|---|
| E1 | Stufe 16 zeigt `failures > 0` | **Ja**, 30 |
| E2 | Stufe 16 unter Stufe 8 bei den Treffern je Anfrage | **Ja**, 4,88 gegen 5,33 |
| E3 | Stufe 8 zeigt `failures == 0` | **Nein**, 9. Acht davon gehen auf den Begriff ohne Treffer, einer bleibt offen |
| E4 | Beide Zählungen stimmen überein | **Wörtlich nein**, 30 gegen 14. Nach Aufschlüsselung der zweiten Ursache deckungsgleich |

E3 und E4 sind verfehlt, und sie bleiben verfehlt. Beide zeigen dasselbe: der
Zähler misst nicht die Abbrüche, sondern die leeren Antworten, und das ist mehr,
als der Name `EmptyResultGroup` einem eiligen Leser sagt. Der Fix ist trotzdem
das, was er sein sollte, weil `min_hits` und `hits_per_request` jetzt in jeder
Rohdatei stehen und die Zahl damit lesbar bleibt. Wer die Abbrüche allein
braucht, braucht weiterhin das Protokoll daneben.

## 4. DI-10-02, nicht geschlossen

**Der Befund.** Das Sprachfall-Skript führt ein eigenes Konto ein, weil der
Lastkorpus dieselben Wörter trägt. Ein eigenes Konto trennt aber die Berechtigung
und nicht den Index. Die Nachfolgefassung sollte den Fremdbestand vor den zehn
Fällen messen und einen Fall, dessen Aussage darin ertrinkt, als nicht messbar
kennzeichnen statt als rot.

**Der Lauf.** `FRIST=60 RUNDEN=10 CI_LAUF=34530208024`, Rückgabewert **17**,
also mindestens ein messbarer Fall rot. Rohdatei `rohdaten/05-sprachfaelle.txt`.

| Fall | Begriff | Fremdbestand (Seite, Tiefe 64) | Urteil |
|---|---|---|---|
| 1 | Genehmigung | 6, 26 | ROT |
| 2 | Frist | 6, 26 | ROT |
| 3 | Mueller | 0, 0 | GRUEN |
| 4 | Vertrag | 6, 26 | ROT |
| 5 | drei Monate | 0, 0 | GRUEN |
| 6 | bescheid | 6, 26 | ROT |
| 7 | type:pdf bescheid | 6, 26 | GRUEN |
| 8 | Belehrung | 0, 0 | GRUEN |
| 9 | Auszug | 0, 0 | GRUEN |
| 10 | Erinnerung | 0, 0 | GRUEN |

Bilanzzeile: `sprachfaelle bestanden 6 von 10, davon 0 nicht messbar`.
`ci-beleg: integration.yml Lauf 34530208024`, eine Laufnummer und kein
Platzhalter, wie DI-10-02 es verlangt.

**Warum kein einziger Fall als nicht messbar gilt.** Der gemessene Fremdbestand
beträgt 26 und liegt damit unter der Schwelle 64. Die Gegenprobe in
`rohdaten/07-fremdbestand-gegenprobe.txt` zeigt, woran das liegt: dieselbe Route
liefert dem Konto `lasttest` für **jeden** geprüften Begriff exakt 26 Treffer,
bei Tiefe 64, 200 und 2000, und exakt 6 Treffer bei Tiefe 5. Die Zahl hängt
weder am Begriff noch an der Tiefe. Sie ist ein Deckel der Antwort und nicht der
Bestand dahinter.

Damit kann die Messgröße die Schwelle 64 nicht überschreiten, und die Vorprüfung
kann auf dieser Instanz kein Urteil der dritten Art auslösen. Das Skript urteilt
wieder zweiwertig, und die vier Fälle 1, 2, 4 und 6 sind rot wie am 10.09.2026.
Die Bilanz `6 von 10` ist zahlengleich mit der des 10.09., und genau das war der
Zustand, den der Fix beenden sollte.

**Die Erwartungen, ohne Nachbesserung.**

| Nr | Erwartung | Eingetreten? |
|---|---|---|
| E5 | Vier Fälle als nicht messbar | **Nein**, null Fälle |
| E6 | Möglicherweise ein fünfter | entfällt, Fall 7 ist grün |
| E7 | Die übrigen bleiben grün, mit Fremdbestand 0 | **Teils.** Fünf grüne Fälle tragen 0, Fall 7 trägt 26 und ist trotzdem grün |
| E8 | Bilanz `6 von 10, davon 4 nicht messbar` | **Nein**, `6 von 10, davon 0 nicht messbar` |

**Was der Fix trotzdem gebracht hat.** Drei der vier Zusagen der
Nachfolgefassung halten: jeder Begriff trägt seine Fremdbestandszahl in einer
eigenen Zeile, die Bilanzzeile nennt zwei Zahlen statt einer, und `CI_LAUF` ist
eine Pflichteingabe, deren Fehlen den Lauf vor dem ersten Fall beendet. Was
nicht hält, ist die vierte: das dreiwertige Urteil bleibt praktisch zweiwertig,
weil die Größe, an der es hängt, die Schwelle nicht erreichen kann.

**Wo der Beweis mit eigenem Index liegt.** In `integration.yml`, Job
`index-search-e2e`, Lauf **34530208024**. Dieser Lauf fährt dieselben zehn Fälle
auf einer frischen Instanz ohne Fremdbestand. Er ist die Hälfte der Aussage, die
diese Box nicht machen kann, und daran hat sich durch diese Anfahrt nichts
geändert.

**Was als Nächstes zu tun ist, und was ausdrücklich nicht.** Die Vorprüfung
braucht eine Messgröße, die nicht am selben Deckel hängt wie die Fälle: die Zahl
der Dokumente im Index, die den Begriff tragen, statt der Zahl der Treffer, die
die Route herausgibt. Das ist eine Änderung am Skript und keine Messung, sie
gehört in einen eigenen Plan, und sie ist in dieser Anfahrt bewusst nicht
gemacht worden. Ein Messskript, das während seines eigenen Laufs nachgebessert
wird, macht jede Zahl daneben unbelegt.

## 5. Was diese Anfahrt nicht besser gemacht hat

1. **DI-10-02 bleibt offen.** Der Fix ist gebaut und gefahren, aber die
   Messgröße trägt ihn nicht. Siehe Abschnitt 4.
2. **DI-10-04 bleibt ungeklärt.** Die Mehrlaufzeit von 26 h 37 min gegen
   18 h 56 min hat zwei Kandidaten, und die Daten entscheiden nicht zwischen
   ihnen. Das entscheidet ein Lauf, der die Einbettung erst nach der Indexierung
   anstößt, oder eine Instrumentierung, die die Wartezeit des Zulaufs
   mitschreibt. Beides ist ein Volllauf über rund 26 Stunden und passt unter
   keinen Vier-Stunden-Deckel.
3. **Der Upgrade-Beweis lag nicht in dieser Anfahrt.** Er braucht eine
   Nextcloud mit 1.0.x, die Box trägt den v1.1-Stand mit dem Messindex, und eine
   zweite Nextcloud am selben Docker-Dienst verbietet D-02 mit einer teuren
   Begründung. Er liegt in Plan 11-07, in CI.
4. **DI-07-03 ist einmal mehr sichtbar geworden und nicht untersucht.** Die eine
   unerklärte leere Antwort auf Stufe 8 passt zu diesem Befund, mehr als eine
   Vermutung ist es nicht, und diese Anfahrt hatte keinen Auftrag, sie zu
   prüfen.
5. **Die Abbruchbedingung war nicht prüfbar, wie sie geschrieben stand.** Der
   Befehl, den sie nennt, kann die Zahl nicht liefern, und die Zahl selbst war
   durch einen Lauf überholt, den derselbe Plan voraussetzt. Das hat eine
   Rückfrage gekostet und rund 1,7 Stunden Laufzeit, die im Deckel Platz hatten.

## 6. Die Rohdateien dieses Laufs

| Datei | Was darin steht |
|---|---|
| `rohdaten/01-lastwerkzeug-stufe16.json` | Stufe 16, 160 Anfragen, mit `min_hits`, `hits_per_request`, `failures` und `failure_kinds` |
| `rohdaten/02-lastwerkzeug-stufe08.json` | Kontrollstufe 8, 80 Anfragen, dieselben Schlüssel |
| `rohdaten/03-nc-protokoll-abbrueche.txt` | die unabhängige Zählung im Protokoll, je Zeitfenster, dazu die gemessene Aufschlüsselung der Lücke |
| `rohdaten/04-bestand-vor-der-messung.txt` | der Bestand vor der Messung und die aufgeschlüsselte Abweichung von der Abbruchbedingung |
| `rohdaten/05-sprachfaelle.txt` | die zehn Fälle, die Fremdbestandszahlen, die Urteile, die Bilanzzeile und der CI-Beleg |
| `rohdaten/06-kosten.txt` | Laufzeit und Kosten dieser Anfahrt gegen den freigegebenen Deckel |
| `rohdaten/07-fremdbestand-gegenprobe.txt` | die Gegenprobe, die zeigt, dass die Vorprüfung einen Antwortdeckel misst |

Die Skripte, mit denen die Zahlen entstanden sind, liegen in `skripte/`:
`00-ablauf.md` mit der vorher aufgeschriebenen Erwartung, `98b-sprachfaelle.sh`
aus Plan 11-03, `71-protokoll.py` für die Zählung nach Vorgang und
`72-fremdbestand.py` für die Gegenprobe. Das Lastwerkzeug ist
`scripts/ops/search_load.py` aus Plan 11-02, byteidentisch auf die Box gebracht
und dort gefahren.

Der gefahrene Stand des Sprachfall-Laufs vom 10.09.2026 liegt unverändert in
`docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh`, und
diese Anfahrt hat kein Byte davon angefasst.
