# Der Ablauf des v1.2-Laufs, in seiner Reihenfolge

Diese Datei ist der Ablaufplan des Laufs im Verzeichnis
`docs/measurements/2026-09-v12-messung/`. Sie beschreibt den Lauf, **bevor** er
stattfindet, und sie ist absichtlich vor der Anfahrt geschrieben: die Erwartung
steht weiter unten mit Zahlen da, damit sie nach der Messung nicht zur Erklärung
des Ergebnisses werden kann.

**Zur Schreibweise.** Die Abschnittsüberschriften stehen ohne Umlaute, weil
Prüfungen und Verweise auf sie zeigen. Der Fließtext benutzt durchgehend echte
Umlaute. Die Skripte dieses Verzeichnisses schreiben ihre Kommentare und
Protokollzeilen in ASCII, weil sie auf einer Box laufen, deren Gebietsschema
niemand garantiert.

Zwei Sätze vorweg, weil sie den Rest tragen:

- **Dieser Lauf beweist zwei Messwerkzeuge und eine Messbedingung, und sonst
  nichts.** Er beweist nicht die Wirkung der Top-up-Route auf die Laufzeit: das
  ist eine eigene Aussage, die einen vollständigen Volllauf braucht und in
  Phase 15 daneben steht. Er beweist auch keine neue Bestzeit, keinen
  Speicherwert und keine Suchgüte.
- **Deckel und Owner-Freigabe fallen in Phase 15 und nicht hier.** Das
  Rechenblatt für den Zeit- und Kostendeckel steht in
  `docs/runbook-messbox.md`, Abschnitt 2, und kommt auf 42 h und 4,90 USD netto
  bei einer ausgewiesenen Untergrenze von 31 h und rund 3,59 USD. Die Freigabe
  mit Datum und Deckel trägt der Owner am Phase-15-Checkpoint ein, bevor die
  erste Minute läuft.

---

## 1. Was dieser Lauf misst

Zwei aufgeschobene Befunde und eine Messbedingung. Keiner der drei ist eine
Aussage über das Erzeugnis: zwei betreffen die Werkzeuge, mit denen gemessen
wird, und einer die Bedingung, unter der gemessen wird. Ein Werkzeug, das die
falsche Größe misst, und eine Bedingung, die niemand protokolliert, machen jede
Zahl daneben unbelegt.

| Befund | Was schiefging | Was der Fix tut | Wo der Fix liegt |
|---|---|---|---|
| **DI-10-02 und DI-11-01** | Die Vorprüfung des Fremdbestands fragte die OCS-Route. Die Gegenprobe vom 10.09.2026 hat dieselbe Route mit vier Tiefen und mit Begriffen gefragt, die in keinem der zehn Fälle vorkommen, und jedes Mal dieselbe Zahl 26 gemessen. 26 ist ein Deckel der Antwort und nicht der Bestand dahinter; die Schwelle 64 war damit unerreichbar, das dreiwertige Urteil fiel auf zweiwertig zurück, und vier Fälle blieben rot statt nicht messbar zu heißen | Der Bestand entsteht im Prozess des Containers über `ranked_sides` und `count`, ungedeckelt, und die Messbarkeit hängt am Rang der eigenen Datei in den beiden Ranglisten statt an einer Trefferzahl | `skripte/73-bestand-sonde.py` (Plan 12-04) und `skripte/98c-sprachfaelle.sh` (Plan 12-05) |
| **Cron-Befund (DI-10-04)** | Der Systemcron stand nominal auf fünf Minuten, die tatsächliche Scheibenauslieferung lag bei rund zwölf Minuten. Der Lauf vom 10.09.2026 war dadurch 5,85 h von 26,6 h ohne Arbeitsvorrat, gerechnet aus 194 von 812 Lesungen gegen eine Baseline von 0,10 h | Ein zweiteiliger, im Skript durchgesetzter Check: ein Konfigurationszweig vor dem Lauf, der das Intervall liest und als Pflichtzeile protokolliert, und ein Wirkungszweig während des Laufs, der den tatsächlichen Abstand zwischen zwei Zulaufscheiben misst. Beide brechen ab, statt weiterzulaufen | `skripte/97-cron-vorpruefung.sh` (Plan 12-06) |

**Warum der Cron-Check zwei Zweige hat und nicht einen.** Ein Vorprüfschritt,
der nur die Konfiguration liest, hätte am 10.09.2026 grün gemeldet, während der
Befund vorlag: die Einstellung war richtig, die Wirkung war es nicht. Eine
Runbook-Checkliste allein reicht ebenfalls nicht, weil menschliche Schritte
vergessen werden; genau das war die v1.1-Falle (D-07 und D-08).

**Worauf die gefahrenen Fassungen zeigen und warum sie hier nicht liegen.** Die
am 10.09.2026 gefahrene Fassung des Sprachfall-Laufs ist
`docs/measurements/2026-09-werkzeugfixe/skripte/98b-sprachfaelle.sh`, und ihre
Vorgängerin liegt im Verzeichnis der Vergleichsmessung. Beide bleiben byteweise
unverändert, weil ein nachträglich bearbeitetes Messskript jede Zahl daneben
unbelegt macht; `backend/tests/test_measurement_scripts.py` hält für beide eine
Prüfsumme. `98c-sprachfaelle.sh` in diesem Verzeichnis ist die Nachfolgefassung.

---

## 2. Die Schrittfolge

Jede Zeile nennt den Schritt, die Rohdatei, die dabei entsteht, und die Aussage,
an der der Schritt hängt. Die Reihenfolge ist bindend: Schritt 1 kann die
Anfahrt beenden, bevor sie nennenswert Geld kostet, und Schritt 5 hängt an einem
Lauf, den Schritt 4 nicht mehr verändern darf.

| Nr | Schritt | Rohdatei | Die Aussage, an der der Schritt haengt |
|---|---|---|---|
| 1 | Anfahrt und Zustandsprüfung nach `docs/runbook-messbox.md`, Abschnitt 4: Wiederaufbau aus dem Snapshot, `/etc/hosts`-Pin, `app_api:app:disable` und `:enable`, harte Speichergrenze aus der cgroup, `free -h`, `nproc`, `uname -m`, `occ findling:index` | `rohdaten/04-bestand-vor-der-messung.txt` | Der Index ist intakt und die Box ist die, gegen die Phase 10 gemessen hat: **52.111 indexiert, 37 uebersprungen, 0 fehlgeschlagen**, 3.9Gi, 2 Kerne, aarch64. Stimmt das nicht, endet die Anfahrt hier |
| 2 | **Cron-Konfigurationszweig:** `./97-cron-vorpruefung.sh vorher`, vor jedem Messblock | `rohdaten/97-cron-vorpruefung-vorher.txt` | Modus und Takt der Instanz stehen als Block im Protokoll: `cron-modus-ist`, `cron-intervall-quelle` und die Pflichtzeile `cron-intervall-ist`. Ein Lauf ohne diese Zahl gilt als unvollständig und endet hier (D-07) |
| 3 | **Bestandsvorlauf der Sonde:** `73-bestand-sonde.py` wandert mit `docker cp` in den Container und läuft ohne `DATEI_IDS`, gefahren als Abschnitt 0 von `98c-sprachfaelle.sh` | Abschnitt 0 in `rohdaten/05-sprachfaelle.txt` | Je Begriff der ungedeckelte Bestand und die Belegung beider Ranglisten, im Prozess gemessen. Die Zahl 26 darf hier nicht mehr auftauchen, sonst misst die Sonde denselben Deckel wie die alte Route |
| 4 | **Sprachfall-Lauf mit Abschnitt 3b:** Laufnummer des letzten grünen `integration.yml`-Laufs holen, dann `CI_LAUF=<nummer> ./98c-sprachfaelle.sh`. Abschnitt 3b fährt die Sonde nach Upload und Indexierung ein zweites Mal, mit den Kennungen aus dem Antwortkopf der Uploads | `rohdaten/05-sprachfaelle.txt` | **Der Beweis von DI-10-02 und DI-11-01:** je Fall ein dreiwertiges Urteil am Rang der eigenen Datei gegen die Schwelle 64, eine Bilanzzeile mit zwei Zahlen und ein `ci-beleg` mit einer Laufnummer |
| 5 | **Cron-Wirkungszweig:** `./97-cron-vorpruefung.sh waehrend`, gestartet mit dem Volllauf und neben ihm laufend | `rohdaten/97-cron-vorpruefung-waehrend.txt` | **Der Beweis der Messbedingung:** `scheiben-erkannt`, `scheibenabstand-min`, `-median` und `-max`, `vorrat-null-in <n>-von-<m>-lesungen` und `ablesereihe-intervall`. Erst diese Zahlen sagen, ob der Zulauf so getaktet hat, wie die Konfiguration behauptet |

**Zwei Vorbedingungen von Schritt 4, die vor der Anfahrt zu klären sind, weil
sie sonst Box-Minuten kosten:** die Laufnummer aus `integration.yml`, ohne die
das Skript mit **22** abbricht, und die Frage, ob die Sonde im Container
gefahren werden kann, ohne die Abschnitt 3b keine Ränge erhebt und der Lauf mit
**24** endet. Der Abbruch mit 22 kommt vor dem ersten Handgriff und kostet
Sekunden; eine nicht fahrbare Sonde fällt schon in Abschnitt 0 als **19**, vor
dem Hochladen der 39 Dateien. Nur **24** selbst fällt erst nach Upload und
Indexierung, weil ein Rang vorher nicht existiert; genau deshalb gehört die
Sondenfrage vor die Anfahrt.

---

## 3. Die Erwartung, vorher aufgeschrieben

Dieser Abschnitt ist der Grund, warum diese Datei vor der Anfahrt entsteht. Was
hier steht, wird nach der Messung **nicht** angepasst.

| Nr | Erwartung | Woher sie kommt |
|---|---|---|
| E1 | **Der Bestand je Begriff liegt über 26**, für mindestens die Begriffe, die im Lastkorpus häufig vorkommen | 26 war der Antwortdeckel der alten Route, gemessen am 10.09.2026 für jeden Begriff und jede der vier Tiefen. Bleibt die neue Zahl bei 26 stehen, misst die Sonde denselben Deckel und nicht den Bestand |
| E2 | **Die Fensterbelegung sättigt bei 100** und wird für häufige Begriffe genau 100 melden | `SEARCH_RRF_WINDOW = 100` in `backend/src/findling/config.py`. Die Sonde liest die beiden Ranglisten in dieser Breite; oberhalb davon ist die Belegung keine Aussage mehr über den Bestand, der Rang der eigenen Datei dagegen bleibt eine |
| E3 | **Mindestens einer der vier am 10.09. roten Fälle ist jetzt messbar** oder wird ausdrücklich als nicht messbar mit einer Rangangabe ausgewiesen | Die Diagnose vom 10.09. hat für alle vier gemessen, dass die eigene Datei nicht in die Kandidatenliste kommt, für `Bescheid` auf Rang 1.925 von 2.000. Ein Rang ist eine Position und kein gedeckelter Zähler: er kann die Schwelle 64 erreichen, die Trefferzahl konnte es nie |
| E4 | **Das protokollierte Cron-Intervall beträgt 300 Sekunden**, und die Zeile `cron-intervall-ist` nennt die Quelle daneben | D-07: der Ablauf setzt den Systemcron der Messinstanz explizit auf fünf Minuten. Weicht der gelesene Wert um mehr als zehn Prozent ab, endet der Schritt mit 26 |
| E5 | **Der gemessene Scheibenabstand liegt unter 420 Sekunden** | Fünf Minuten Systemcron plus Spielraum. Die rund zwölf Minuten des v1.1-Laufs, also rund 720 Sekunden, liegen deutlich darüber; genau diese Lücke hat 5,85 h Leerlauf gekostet |
| E6 | **Die Ablesereihe des Wirkungszweiges ist mit ihrem Intervall benannt**, also 120 Sekunden in der Zeile `ablesereihe-intervall` | In v1.1 haben zwei Ablesereihen zwei verschiedene Prozentzahlen für denselben Sachverhalt erzeugt: 194 von 812 Lesungen in `docs/performance.md` gegen 62 von 325 Lesungen in der Rohdatei desselben Laufs, also rund 24 gegen 19 Prozent |
| E7 | **Der Bericht sagt, WELCHE Reihe seine Protokollzahl liefert**, statt beide Prozentzahlen nebeneinanderzustellen | Die Zuordnung der beiden Reihen zu den beiden Beobachtern (alle 120 s gegen alle 300 s) ist plausibel, aber nicht belegt; sie ist Annahme A1. Eine Zahl ohne ihre Reihe wäre Scheingenauigkeit |

**Eine verfehlte Erwartung ist ein Ergebnis und kein Grund für eine zweite
Anfahrt.** Das gilt besonders für E3 und E5. Wenn der Scheibenabstand diesmal
unter dem Deckel bleibt, ist der v1.1-Befund dadurch weder widerlegt noch
erklärt: die Instanz ist aus einem Snapshot neu aufgebaut, und die Top-up-Route
ist seit v1.1 dazugekommen. Genau dieser Satz gehört dann in den Bericht.

---

## 4. Woran der Lauf abgebrochen wird

| Bedingung | Wo sie greift | Folge |
|---|---|---|
| `occ findling:index` zeigt nicht 52.111 / 37 / 0 | Schritt 1, vor jeder Messung | Die Anfahrt endet, der Ist-Stand geht nach `04-bestand-vor-der-messung.txt`, der Owner entscheidet neu |
| Nicht alle 39 Dateien hochgeladen | Schritt 4 | Rückgabewert **15** |
| Arbeitsvorrat am Rundendeckel nicht leer | Schritt 4 | Rückgabewert **16**. Die Fälle 8 bis 10 hängen an der OCR-Spur; dieser Block ist abbrechbar und keine Vorbedingung des Berichts |
| Mindestens ein **messbarer** Fall ist rot | Schritt 4 | Rückgabewert **17**. Nicht messbare Fälle zählen hier ausdrücklich nicht mit |
| `jq` fehlt auf der Box | Schritt 4 | Rückgabewert **18** |
| Die Bestandsmessung im Container konnte nicht fahren | Schritt 3, Abschnitt 0 des Skripts | Rückgabewert **19**. Der Abbruch kommt vor dem Hochladen der 39 Dateien |
| `CI_LAUF` trägt keine Laufnummer | Schritt 4, vor dem ersten Fall | Rückgabewert **22** |
| Kein einziger Fall war messbar | Schritt 4 | Rückgabewert **23**. Ein Lauf, in dem jeder Begriff im Fremdbestand ertrinkt, ist eine Aussage über die Instanz und keine über die Sprachkette |
| Abschnitt 3b konnte keine Datei-Kennungen erheben oder die Sonde lief nicht | Schritt 4, zwischen Indexierung und Fällen | Rückgabewert **24**. Ohne Ränge hießen alle zehn Fälle nicht messbar, und zwar aus dem falschen Grund |
| Die Cron-Konfiguration war auf keiner der bekannten Quellen lesbar | Schritt 2, unterhalb der Pipeline | Rückgabewert **25**. Ein Lauf ohne protokolliertes Intervall gilt als unvollständig (D-07) |
| Das gelesene Intervall weicht um mehr als zehn Prozent vom Soll ab | Schritt 2, unterhalb der Pipeline | Rückgabewert **26**. Die Messbedingung ist dann nicht hergestellt, und der Laufzeitvergleich wäre unbelegt |
| Der Wirkungszweig wurde nicht gefahren oder hat keine Zahl erzeugt | Schritt 5, unterhalb der Pipeline | Rückgabewert **27**. Weniger als zwei erkannte Scheiben ergeben keinen Abstand, und ein Wirkungszweig ohne Zahl ist kein Protokoll |
| Der gemessene Scheibenabstand liegt über 420 Sekunden | Schritt 5, unterhalb der Pipeline | Rückgabewert **28**. Das ist ein Befund und keine Störung: die Anfahrt hält hier, statt eine unvergleichbare Laufzeit zu erzeugen |

Die Rückgabewerte 15 bis 19 und 22 bis 24 sind die von `98c-sprachfaelle.sh` und
stehen unverändert so, wie die Vorgängerfassung sie vergeben hat, damit ein
Abbruch dieses Laufs und ein Abbruch vom 10.09. dasselbe bedeuten. Neu sind
allein 25 bis 28, und sie setzen den Katalog fort, statt ihn zu verschieben.
Jeder dieser vier Abbrüche steht **unterhalb** der `tee`-Pipeline seines
Skripts: der Rückgabewert einer Pipeline gehört zu `tee`, und ein Abbruch
innerhalb des Blocks verließe nur die Subshell. Die Verweigerung wäre dann eine
Zeile in einer Rohdatei, die niemand liest.

---

## 5. Nach dem Lauf

Rohdaten und Skripte committen, den kurzen Bericht in `../README.md` schreiben,
die Box nach Abschnitt 5 des Runbooks anhalten und die Kosten dem freigegebenen
Deckel gegenüberstellen. In den Bericht gehören die drei Protokollblöcke
wörtlich: der Block des Konfigurationszweiges, der Block des Wirkungszweiges und
die Bilanzzeile der Sprachfälle mit ihren beiden Zahlen. Dazu ein Abschnitt
"Was dieser Lauf nicht besser gemacht hat".

Sobald `98c-sprachfaelle.sh` und `97-cron-vorpruefung.sh` gefahren sind, gehört
für beide ein Prüfsummen-Wächter in `backend/tests/test_measurement_scripts.py`,
wie ihn die beiden älteren Fassungen tragen: eine gefahrene Messfassung ist Teil
des Belegs und wird danach nicht mehr angefasst.

Vor dem Fertigmelden läuft das Vokabular-Gate lokal über die Dateien dieses
Verzeichnisses, wie über jede nach außen sichtbare Datei dieses Projekts.
