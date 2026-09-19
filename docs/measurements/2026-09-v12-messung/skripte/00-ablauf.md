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

**Nachtrag vom 19.09.2026, zur Geltung dieser Datei.** Die beiden Sätze oben
sind vor der Phase 15 geschrieben worden und bleiben stehen, weil sie den
ursprünglichen Zuschnitt dieses Laufs benennen. Seit der Planung der Phase 15
ist dieser Lauf **die Anfahrt selbst**: er beweist zusätzlich die vier offenen
Messaufträge des Milestones, also die Wirkung der Top-up-Route auf die Laufzeit,
die Wiederaufwärm-Kosten der Entladung (MEM-01), die Rückkehr zur Grundlast nach
einem Indexlauf (MEM-02) und den Filter- und Sortierblock auf dem Vollbestand
(D-01). Der alte Satz wird dadurch nicht falsch, sondern eng: er beschreibt den
Lauf, wie er am 14.09.2026 geplant war, und nicht den, der gefahren wird. Was er
weiterhin richtig sagt, ist die Trennung selbst: eine Aussage über die Werkzeuge
ist keine über das Erzeugnis, und keine der beiden wird der anderen
zugeschlagen.

**Der Deckel ist seit dem 19.09.2026 neu gerechnet.** Die Zahl oben, 42 h und
4,90 USD netto, ist der Vorgängerstand vom 16.09.2026. Das Rechenblatt in
`docs/runbook-messbox.md`, Abschnitt 2, steht seit Plan 15-02 auf **46 h und
5,40 USD netto**, weil drei Posten dazugekommen sind, die im alten Blatt
vollständig fehlten: der Abbildwechsel, der MEM-02-Block und der Filter- und
Sortierblock. Der Vorgängerstand bleibt sichtbar, damit die Differenz ablesbar
ist und nicht nur die Steigerung. Freigegeben wird die Zahl weiterhin vom Owner,
mit Datum, am Checkpoint der Phase 15 und vor der ersten Minute.

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

### 2.1 Nachtrag vom 19.09.2026: die Schrittfolge der Anfahrt, zwoelf Zeilen

Die fünf Schritte oben bleiben im Wortlaut stehen. Sie sind die Fassung, die den
Beweis der zwei Messwerkzeuge und der einen Messbedingung trägt, und ihre
Unverändertheit ist Teil ihres Werts. Bindend für die Anfahrt ist die Tabelle
darunter: sie nummeriert nach `docs/runbook-messbox.md`, Abschnitt 7, damit
beide Dateien im Gleichschritt stehen, mit denselben Schrittnummern, denselben
Werkzeugen und denselben Rückgabewerten.

**Von den fünf alten Nummern wandert genau eine.**

| Alte Nummer | Neue Nummer | Schritt |
|---|---|---|
| 1 | 1 | Zustandsprüfung und Nullstandsbeleg |
| 2 | 2 | Cron-Konfigurationszweig |
| 3 | 3 | Bestandsvorlauf der Sonde |
| 4 | **7** | Sprachfall-Lauf mit Abschnitt 3b |
| 5 | 5 | Cron-Wirkungszweig |

Wo oben "Schritt 4" steht, ist also der Sprachfall-Lauf gemeint und nicht der
Volllauf; die beiden Vorbedingungen, die der Absatz darüber nennt, gehören
unverändert zu ihm. Die neue Nummer 4 ist der Volllauf, den die alte Tabelle
nicht als eigenen Schritt führte, weil er dort nur der Träger des
Wirkungszweiges war.

| Nr | Schritt | Werkzeug | Rohdatei | Die Aussage, an der der Schritt haengt |
|---|---|---|---|---|
| 0 | **Abbildwechsel auf den v1.2-Stand**, vor der Zustandsprüfung und genau einmal | `ABBILD_DIGEST="sha256:<hex>" ./92b-wechsel.sh` | `92b-wechsel.txt`, `40b-baumhash.txt` | Der gemessene Stand ist benannt: `baumhash-gleich ja`, der zurückgelesene Digest im Protokoll, beide cgroup-Felder auf 2147483648. Ohne diese Zeilen gehört jede Zahl danach zu einem Zustand, den niemand benennen kann |
| 1 | Zustandsprüfung und Nullstandsbeleg | `./93-nullstand.sh`, `occ findling:index --restart -n` | `04-bestand-vor-der-messung.txt`, `93-nullstand.txt` | 52.111 indexiert, 37 übersprungen, 0 fehlgeschlagen, 3.9Gi, 2 Kerne, aarch64, und nach dem Zurücksetzen ein abgelesener Nullstand. Stimmt eines davon nicht, endet die Anfahrt hier |
| 2 | Cron-Konfigurationszweig, vor jedem Messblock | `./97-cron-vorpruefung.sh vorher` | `97-cron-vorpruefung-vorher.txt` | Modus und Takt der Instanz stehen als Block im Protokoll, mit der Pflichtzeile `cron-intervall-ist` und ihrer Quelle |
| 3 | Bestandsvorlauf der Sonde | Abschnitt 0 von `./98c-sprachfaelle.sh`, das `73-bestand-sonde.py` in den Container trägt | Abschnitt 0 in `05-sprachfaelle.txt` | Je Begriff der ungedeckelte Bestand und die Belegung beider Ranglisten, im Prozess gemessen. Die Zahl 26 darf hier nicht mehr auftauchen |
| 4 | **Volllauf beider Spuren**, detached gestartet | `./96-volllauf.sh`, daneben `./96b-waechter.sh` | `96-volllauf.csv`, `96b-waechter.txt` | Die Laufzeit bis zum letzten Vektor, gegen die 26 h 37 min des v1.1-Laufs. Das ist der Wirkungsbeleg der Top-up-Route und die längste Einzelzeile des Deckels |
| 5 | Cron-Wirkungszweig, mit dem Volllauf gestartet und neben ihm laufend | `./97-cron-vorpruefung.sh waehrend` | `97-cron-vorpruefung-waehrend.txt` | Der Beweis der Messbedingung: Scheibenabstand, die Zahl der Lesungen ohne Vorrat und die Ablesereihe mit ihrem Intervall |
| 6 | Laststufen 1, 4, 8, 12 und 16, je mit einem Entscheid zu den regressiven Stufen | `./95-spitze.sh`, `./97-nebenlaeufigkeit.sh` über `scripts/ops/search_load.py` | `95-*.json`, `95-*.csv`, `97-nebenlaeufigkeit.txt` | Die p95-Reihe gegen das Gruppenbudget von 2.500 ms. Eine Stufe ohne Antwortzahlen wird als solche protokolliert und nicht geschätzt |
| 6b | **Filter- und Sortierblock:** Sortierung auf grossem Bestand, Blättern unter Filter | `./99c-filter-sortierung.sh` | `99c-filter-sortierung.txt` | Erstmessung ohne Vergleichszeile: was `newest` und `oldest` auf dem Vollbestand kosten, und ob der Cursor über drei Seiten hält |
| 7 | **Sprachfall-Lauf mit Abschnitt 3b** | `CI_LAUF=<laufnummer> ./98c-sprachfaelle.sh` | `05-sprachfaelle.txt` | Der Beweis von DI-10-02 und DI-11-01: je Fall ein dreiwertiges Urteil am Rang gegen die Schwelle 64, eine Bilanzzeile mit zwei Zahlen und ein `ci-beleg` mit einer Laufnummer |
| 8 | **Wiederaufwärm-A/B**, vier Ausprägungen, je Lauf genau eine | `./95b-wiederaufwaermen.sh 1` bis `./95b-wiederaufwaermen.sh 4` | `95b-wiederaufwaermen-1.txt` bis `95b-wiederaufwaermen-4.txt` | Was die Entladung aus MEM-01 an Nachladezeit kostet, gemessen als Kreuz aus zwei Schalterstellungen und zwei Zuständen des Seitencaches |
| 8b | **MEM-02:** Rückkehr zur Grundlast nach einem Indexlauf | `./94b-grundlast-rueckkehr.sh` | `94b-grundlast-rueckkehr.txt` | Ob beide Speicherhalter nach Ablauf der Frist wieder frei sind, und ausdrücklich nicht, um wie viel eine Zahl gefallen ist |
| 9 | Endmessungen und Gegenproben, vor jedem zerstörenden Schritt | `./90-bestand.sh`, der Vektorbestand, die Kostenzeilen aus `box.env` | `90-bestand.txt`, `96-vektorbestand.txt`, `93-kosten-und-verbleib.txt` | Was hier nicht erhoben ist, ist nach dem Abbau nicht mehr erhebbar. Dieser Schritt ist die Vorbedingung der Abbau-Checkliste |

**Zur Aufrufform, einheitlich fuer alle Werkzeuge.** Vierzehn der achtzehn
Werkzeuge dieses Verzeichnisses stehen mit der Rechtemaske `100644` im Index,
nur `96-volllauf.sh`, `96b-waechter.sh`, `96c-lesen.py` und
`96d-statusbeobachter.py` mit `100755`. Ein Auscheck auf der Box erbt genau
diese Masken, und der erste Aufruf `./97-cron-vorpruefung.sh vorher` endete dort
mit **126** und "Permission denied", in der bezahlten Zeit und mit einer
Meldung, die in keinem der beiden Dokumente erklärt ist. Die Auflösung ist eine
Zeile, einmal im Laufverzeichnis der Box, **vor Schritt 0**, und ihre
Rückleseprobe gehört in die Rohdatei des Abbildwechsels:

```sh
cd <checkout>/docs/measurements/2026-09-v12-messung/skripte
chmod +x *.sh *.py
ls -l | awk '{ print $1, $NF }'
```

Danach gilt in dieser Datei und im Runbook **eine** Form: `./werkzeug.sh`, mit
den Umgebungsvariablen davor und den Argumenten dahinter. Die Form
`sh werkzeug.sh` bleibt der Weg, auf dem ein Werkzeug ein anderes ruft, so wie
`92b-wechsel.sh` den Baumhashbeweis `40b-baumhash.sh` ruft; sie braucht keine
Rechtemaske und ist dort die richtige. Für den Operator ist sie es nicht, weil
zwei Formen nebeneinander die eine Frage offenlassen, welche von beiden gilt.

### 2.2 Kalt wird hergestellt, nicht bewahrt

Schritt 3 fährt über die Diagnose-Route und wärmt damit den Container, und
Schritt 6 lädt das Modell absichtlich vor der Reihe. Beide liegen vor Schritt 8,
und beide sind nicht verschiebbar. Die Kaltmessungen des Schrittes 8 laufen
deshalb **nach Schritt 6 und 7**, und jede von ihnen beginnt mit einem
Containerneustart, einer gefahrenen Ruhezeit und danach dem geleerten
Wirtscache. Gemeint ist damit ein Befehl und kein Wort, **auf dem Wirt und nicht
im Container**: `sync`, dann der Wert `3` nach `/proc/sys/vm/drop_caches`, dann
`free -h` als Rückleseprobe, deren Ausgabe in die Rohdatei gehört.

**Die Nebenwirkung steht daneben und nicht im Bericht danach.** Das Leeren
verwirft auch den mmap-Cache des Tantivy-Index. Die kalte Suche misst damit
**beide Hälften kalt**, die Semantik und den Volltext, und nicht allein das
Nachladen der Gewichte. Das ist die gewollte schlechtere Hälfte der Wahrheit:
sie ist der Fall, den ein Nutzer nach einem Neustart der Box wirklich bekommt,
und sie muss im Bericht dastehen, sonst liest sich eine Zahl als
Wiederaufwärmkosten, die zum Teil Indexkosten sind.

Diese Zeile steht hier, **bevor** die Box steht, weil sie die Messung definiert
und nicht erklärt. Eine Reihenfolge, die nach der Messung begründet wird, ist
keine Reihenfolge, sondern eine Auswahl.

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

### 3.1 Nachtrag vom 19.09.2026: die Erwartungen E8 bis E14

Sieben weitere Erwartungen, je mit ihrer Zahl und ihrer Herkunft, und aus
demselben Grund wie die sieben oben: sie stehen vor dem Lauf, und der Commit
dieser Datei ist ihr Zeitstempel. Der Satz "eine verfehlte Erwartung ist ein
Ergebnis" gilt für sie unverändert mit.

- **E8, Abbildwechsel.** Nach dem Wechsel meldet `40b-baumhash.sh`
  `baumhash-gleich ja`, und der aufgelöste Digest steht als protokollierte Zeile
  daneben. Herkunft: Befund L-05 der Phase 11 und der Abschnitt 6 des Runbooks.
  Der Digest ist die Notiz und der Baumhash der Beweis; ein Lauf gegen ein
  Abbild, dessen Stand niemand benennen kann, misst nichts Nennbares.

- **E9, Volllauf.** Die Laufzeit beider Spuren liegt **unter 26 h 37 min**.
  Herkunft: der v1.1-Lauf brauchte genau so lange und war davon 5,85 h ohne
  Arbeitsvorrat, und die Top-up-Route ist genau dagegen gebaut. Dies ist
  ausdrücklich eine Erwartung und **kein Planwert**: der Deckel rechnet weiter
  mit 26 h 37 min, weil ein Planwert, der eine Verbesserung vorwegnimmt, genau
  der Fehler ist, der den v1.1-Deckel gerissen hat.

- **E10, Laststufen.** Die Stufen 1 und 4 halten das Gruppenbudget von
  2.500 ms, die Stufe 8 hält es mit **kleinerer Reserve als 374,5 ms**, und die
  Stufen 12 und 16 reissen es weiterhin. Herkunft: die Reihe aus
  `docs/audits/2026-09-phase-11/` mit 464,3 ms, 1.068,0 ms, 2.125,5 ms,
  3.453,4 ms und 4.446,2 ms. **Die neuen Zahlen dürfen schlechter aussehen**,
  und das wäre kein Befund über die Suche: seit dem 10.09.2026 zählt der Zähler
  abgebrochene Aufrufe nicht mehr als beantwortet (DI-10-01), also misst er
  denselben Zustand strenger.

- **E11, Filter und Sortierung.** `newest` und `oldest` antworten auf dem
  Vollbestand nicht um mehr als den **Faktor zwei** langsamer als `relevance`,
  und drei geblätterte Seiten melden die Seitenzahlen **1, 2, 3** ohne eine
  Datei-Kennung zweimal. Herkunft: der Sortierzweig ist rein lexikalisch und
  trägt keine Vektorhälfte (13-02), und der Cursor-Fingerabdruck hält oder er
  hält nicht (13-08). Dies ist eine **Erstmessung ohne Vergleichszeile**: es
  gibt keinen v1.1-Wert, neben den diese Zahlen im Bericht geraten dürften.

- **E12, Wiederaufwärmen.** Die erste Suche nach einer Entladung bleibt **unter
  1,5 s**. Herkunft: auf der Entwicklungsmaschine 1,37 bis 1,44 s gegen warm
  0,41 bis 0,48 s, und die Box ist langsamer als sie. **Ein Reissen ist hier ein
  Ergebnis und keine Störung:** die Marge war schon bei der Abnahme der Phase 14
  ausdrücklich als dünn benannt, und die Zahl der Box ist genau die, wegen der
  sie benannt wurde.

- **E13, MEM-02.** Die Rückkehr zur Grundlast nach einem Indexlauf liegt **über
  300 MB**, und der Bodensatz, der nicht zurückkommt, liegt bei **rund 16 MB**.
  Herkunft: 376,3 MB Rückgabe in der Sichtprobe aus 14-12 auf einer Maschine
  ohne `malloc_trim`, und 17,1 MB Zielast über fünf Zyklen im Vorprüflauf auf
  aarch64, davon 15,9 MB allein im ersten Zyklus.

- **E14, das Belegkriterium fuer den Vorschlagswert 900 s.** Belegt werden die
  **Folgen** einer Frist und nie die Frist selbst. Der Vorschlagswert bleibt bei
  900 s, wenn **beide** Bedingungen halten: die Rückkehr zur Grundlast liegt
  über 300 MB (E13) **und** die erste Suche nach einer Entladung bleibt unter
  1,5 s (E12).
  - **Reisst E12**, wird der Vorschlagswert nicht korrigiert. Seine Empfehlung
    bekommt die gemessene Zahl der Box daneben und den Satz, für welche
    Instanzen er nicht taugt. Eine Frist, die Speicher freigibt und dafür die
    erste Suche über die Decke hebt, ist ein Tausch und keine Einstellung.
  - **Reisst E13**, ist die Frist die falsche Stellschraube, und der Befund
    gehört an die Entladung selbst und nicht an ihren Zeitpunkt. Ein Schalter,
    nach dessen Ablauf nichts zurückkommt, wird nicht anders terminiert, sondern
    in Frage gestellt.
  - **Die verkürzte Ruhezeit ändert daran nichts.** Die Messung stellt die Frist
    auf 60 bis 120 s statt auf 900 s (D-02, Owner-Entscheid vom 19.09.2026) und
    misst damit **denselben Mechanismus** bei einem Bruchteil der Box-Zeit. Das
    ist die Begründung, die im Protokoll steht, und die einzige Einschränkung
    ist, dass diese Messung über die **Häufigkeit** von Entladungen im Alltag
    nichts sagt. Der Vorschlagswert 900 s selbst bleibt eine gekennzeichnete
    Schätzung (Owner-Entscheid aus 14-12).

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

### 4.1 Nachtrag vom 19.09.2026: die Abbruchwerte 29 bis 39

Elf weitere Bedingungen, in derselben Form und mit denselben Nummern wie in
`docs/runbook-messbox.md`, Abschnitt 7.1. Auch sie setzen den Katalog fort,
statt ihn zu verschieben: eine einmal vergebene Zahl wird nicht umgehängt, damit
eine Rohdatei aus einem früheren Lauf lesbar bleibt. Deshalb steht 6b bei 34 und
35, obwohl es vor 8b läuft, das bei 31 bis 33 steht.

| Bedingung | Wo sie greift | Folge |
|---|---|---|
| Die Stellung des Entladeschalters war für einen Messschritt nicht ablesbar | Schritt 8, und vor jedem anderen Messblock | Rückgabewert **29**. Ein Lauf ohne protokollierte Stellung gilt als unvollständig, wie einer ohne Cron-Intervall (Abschnitt 6.4 des Runbooks) |
| Vor einer Kaltmessung wurde die Diagnose-Route gerufen | Schritt 8, vor Ausprägung 1 oder 3 | Rückgabewert **30**. Die Route lädt das Modell, weil sie keine Nutzerroute ist. Die Messung wird wiederholt oder mit dem Aufwärmeffekt im Protokoll gefahren, nie herausgerechnet |
| Der Ast mit eingeschaltetem Schalter hat keine Entladung erlebt | Schritt 8, Ausprägung 1 und 2 | Rückgabewert **31**. Kein `unloaded` und kein Entladezähler über null heisst: gemessen würde das Nachwärmen von etwas, das nie losgelassen wurde |
| Die Grundlast vor dem Indexlauf wurde nicht abgetastet | Schritt 8b, vor dem Anstoss | Rückgabewert **32**. Eine Rückkehr ohne den Wert, zu dem zurückgekehrt wird, ist keine Messgrösse, sondern eine Zahl |
| Der Container wurde zwischen den beiden Abtastungen neu gebaut | Schritt 8b, zwischen den Abtastungen | Rückgabewert **33**. Ein neu gebauter Container startet auf seiner Grundlast, und die Differenz wäre dann ein Neustart und keine Freigabe |
| Die Sortierung lief gegen einen Bestand, der noch wuchs | Schritt 6b, vor der ersten Stufe | Rückgabewert **34**. Die Endzahl des Volllaufs muss stehen, sonst misst die Sortierung zwei verschiedene Bestände unter einer Zahl |
| Eine Filter- oder Sortierstufe lieferte keine Antwortzahlen, oder zwei aufeinander folgende Seiten trugen dieselbe Datei-Kennung | Schritt 6b | Rückgabewert **35**. Ein Blättern, das eine Kennung zweimal ausliefert, ist ein Befund über die Seitenroute und keine Sortierzahl |
| Der Baumhash fehlt, ist nicht dreifach verankert oder meldet `baumhash-gleich nein`, oder der Container läuft nach der Registrierung auf einer anderen Abbildkennung als der geprüften | Schritt 0, vor der ersten Messung und noch einmal unmittelbar danach | Rückgabewert **36**. Jede Zahl danach gehörte zu einem Zustand, den niemand benennen kann |
| Mehr als eine Nextcloud läuft an diesem Docker-Dienst, oder die Zählung war nicht lesbar | Schritt 0, unmittelbar vor jedem `unregister --rm-data` | Rückgabewert **37**. Der Volumenname folgt allein aus der App-Kennung; am 07.09.2026 hat genau das ein Messvolumen gekostet. Eine unlesbare Zählung gilt als ungleich eins |
| Der Arbeitsbaum auf der Box ist nicht sauber | Schritt 0, vor dem Pull | Rückgabewert **38**. Ein Baumhash gegen einen veränderten Arbeitsbaum belegt nichts |
| Die harte Grenze hat die Registrierung nicht überlebt | Schritt 0, nach der Registrierung | Rückgabewert **39**. Gelesen wird aus der cgroup, erwartet werden 2147483648 in beiden Feldern; jede andere Zahl misst eine andere Maschine als v1.1 |

**Der Schlussabsatz oben gilt unverändert weiter, und die elf neuen Werte stehen
ebenfalls unterhalb der `tee`-Pipeline ihres Skripts.** Der Rückgabewert einer
Pipeline gehört zu `tee`; ein Abbruch innerhalb des Blocks verliesse nur die
Subshell, und die Verweigerung wäre eine Zeile in einer Rohdatei statt ein
Abbruch.

**Die eine Ausnahme ist die Verweigerung vor der ersten Zeile.** Fünf Werkzeuge
prüfen ihre Pflichtangabe, bevor eine Rohdatei entsteht, und enden mit **2** und
der Benutzung auf stderr: `92b-wechsel.sh` ohne `ABBILD_DIGEST`,
`95b-wiederaufwaermen.sh` ohne Ausprägung, `97-cron-vorpruefung.sh` ohne Zweig
und `94b-grundlast-rueckkehr.sh` wie `99c-filter-sortierung.sh` mit einem
Argument, das sie nicht kennen. Dieser Abbruch steht mit Absicht **oberhalb**
der Pipeline: ein Lauf, der vor seiner ersten Messung endet, soll keine Rohdatei
hinterlassen. `98c-sprachfaelle.sh` bleibt die Ausnahme davon mit **22** für die
fehlende Laufnummer, weil diese Zahl aus der gefahrenen Vorgängerfassung stammt
und nicht umgehängt wird.

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

**Nachtrag vom 19.09.2026: fuer welche Werkzeuge ein Waechter nachgezogen
wird.** Der Absatz oben nennt zwei Skripte, weil es damals zwei waren. Gefahren
werden auf dieser Anfahrt sechs neue oder fortgeschriebene Fassungen, und für
jede von ihnen gehört nach dem Lauf eine Prüfsumme in
`backend/tests/test_measurement_scripts.py`, wie sie die älteren Fassungen
tragen:

- `98c-sprachfaelle.sh`
- `97-cron-vorpruefung.sh`
- `95b-wiederaufwaermen.sh`
- `94b-grundlast-rueckkehr.sh`
- `99c-filter-sortierung.sh`
- `92b-wechsel.sh`

Der Grund ist derselbe wie bei den beiden Vorgängerinnen und er ist keine
Formalie: eine gefahrene Messfassung ist Teil des Belegs und wird danach nicht
mehr angefasst. Ein Wächter, der erst nach der ersten Nachbesserung entsteht,
schützt die falsche Fassung.
