# Der Ablauf der Werkzeug-Anfahrt, in seiner Reihenfolge

Diese Datei ist der Ablaufplan des Laufs im Verzeichnis
`docs/measurements/2026-09-werkzeugfixe/`. Sie beschreibt den Lauf, **bevor** er
stattfindet, und sie ist absichtlich vor der Anfahrt geschrieben: die Erwartung
steht weiter unten mit Zahlen da, damit sie nach der Messung nicht zur
Erklaerung des Ergebnisses werden kann.

Zwei Saetze vorweg, weil sie den Rest tragen:

- **Diese Anfahrt beweist zwei Werkzeug-Fixe gegen den echten Lastkorpus und
  sonst nichts.** Kein Indexneuaufbau, kein Upgrade-Beweis, keine zweite
  Nextcloud am selben Docker-Dienst. Der Upgrade-Beweis liegt in CI (Plan
  11-07), und eine zweite Instanz hat am 07.09.2026 mit
  `app_api:app:unregister --rm-data` das Messvolumen der ersten geloescht.
- **Der Deckel steht vor dem Start und lautet rund 4 Stunden und 0,50 USD**
  (D-01). Laufender Satz 0,1158 USD je Stunde, also 0,46 USD fuer vier Stunden.
  Geparkt kostet die Box weiter 0,3130 USD je Tag; die Anfahrt ersetzt diese
  Kosten nicht, sie kommt dazu. Die Freigabe des Owners mit Datum und Deckel
  steht in `../README.md`, bevor die erste Minute laeuft.

---

## 1. Was dieser Lauf misst, und warum es zwei getrennte Bloecke sind

Zwei aufgeschobene Befunde aus Phase 10, beide ueber Messwerkzeuge und keiner
ueber das Erzeugnis. Ein Fix an einem Messwerkzeug, der nur lokal gruen ist, ist
eine Aussage ueber das Werkzeug und keine ueber die Messung, die es macht.

| Befund | Was schiefging | Was der Fix tut | Wo der Fix liegt |
|---|---|---|---|
| **DI-10-01** | `search_load.py` zaehlte eine Ergebnisgruppe ohne Containerteil als Erfolg. Die Rohdatei `2026-09-vergleichsmessung-m7g/rohdaten/97-stufe-16.json` meldet `"failures": 0` ueber 160 Anfragen, waehrend das Nextcloud-Protokoll im selben Fenster 17 Abbrueche mit `cURL error 28` traegt | Eine Gruppe mit weniger als `--min-hits` Treffern ist der Fehlschlag `EmptyResultGroup`; `hits_per_request` und `min_hits` stehen im Bericht | `scripts/ops/search_load.py`, Plan 11-02 |
| **DI-10-02** | `98-sprachfaelle.sh` fuehrt ein eigenes Konto ein, weil der Lastkorpus dieselben Woerter traegt. Ein eigenes Konto trennt aber die Berechtigung und nicht den Index: der Vorfilter rankt ueber den ganzen Bestand, der Recheck filtert erst danach. Vier Faelle waren rot, ohne dass ein Sprachdefekt vorlag | Vorpruefung des Fremdbestands vor den zehn Faellen, dreiwertiges Urteil (`GRUEN`, `ROT`, `NICHT MESSBAR`), Bilanzzeile mit zwei Zahlen, `CI_LAUF` als Pflichteingabe | `skripte/98b-sprachfaelle.sh`, Plan 11-03 |

**Worauf das Original zeigt und warum es hier nicht liegt.** Die gefahrene
Fassung des Sprachfall-Laufs vom 10.09.2026 ist
`docs/measurements/2026-09-vergleichsmessung-m7g/skripte/98-sprachfaelle.sh`.
Sie bleibt byteweise unveraendert, weil ein nachtraeglich bearbeitetes
Messskript jede Zahl daneben unbelegt macht. `98b-sprachfaelle.sh` in diesem
Verzeichnis ist die Nachfolgefassung, ihr Kopf verweist auf das Original, und
`backend/tests/test_measurement_scripts.py` haelt den sha256 des Originals als
Waechter. Dasselbe gilt fuer die Rohdaten: die Zahlen vom 09. und 10.09. bleiben
dort stehen, wo sie entstanden sind, auch die Bilanz `6 von 10`.

---

## 2. Die Schrittfolge

Jede Zeile nennt den Schritt, die Rohdatei, die dabei entsteht, und die Aussage,
an der der Schritt haengt. Die Reihenfolge ist bindend: Schritt 2 kann die
Anfahrt beenden, bevor sie etwas kostet, und Schritt 5 haengt an einem
Zustand, den Schritt 4 nicht mehr veraendern darf.

| Nr | Schritt | Rohdatei | Die Aussage, an der der Schritt haengt |
|---|---|---|---|
| 1 | Freigabe des Owners mit Deckel, **vor** `aws_box.sh start` | `../README.md`, Zeile `Anfahrt freigegeben: <Datum>, Deckel <h> h / <USD> USD (D-01)` | Eine Anfahrt ohne Deckel ist eine offene Rechnung. Der Abbau der Box ist ausdruecklich nicht Teil dieser Freigabe (D-03, Plan 11-12) |
| 2 | Anfahrt und Zustandspruefung: `aws_box.sh start`, `/etc/hosts`-Pin auf die aktuelle Adresse des Apache-Containers, `app_api:app:disable` und `:enable` (DI-05-36), harte Speichergrenze aus der cgroup, `free -h`, `nproc`, `uname -m`, `occ findling:index --status` | `rohdaten/04-bestand-vor-der-messung.txt` | Der Index ist intakt und die Box ist die, gegen die Phase 10 gemessen hat: **52.111 indexiert, 37 uebersprungen, 0 fehlgeschlagen**, 3.9Gi, 2 Kerne, aarch64. Stimmt das nicht, endet die Anfahrt hier |
| 3 | **Messblock A, Stufe 16:** `search_load.py --concurrency 16 --rounds 10 --limit 5 --container nc_app_findling_backend`, also 160 Anfragen wie am 10.09. | `rohdaten/01-lastwerkzeug-stufe16.json` | Der neue `failures`-Zaehler an der Stufe, an der die 17 Abbrueche entstanden. Startzeitstempel notieren |
| 4 | **Messblock A, Kontrollstufe 8:** dieselben Parameter, 80 Anfragen | `rohdaten/02-lastwerkzeug-stufe08.json` | Die Gegenprobe. Ohne sie waere ein Zaehler, der immer zaehlt, von einem Zaehler, der richtig zaehlt, nicht zu unterscheiden. Endzeitstempel notieren |
| 5 | **Messblock A, die unabhaengige Zaehlung:** Ausschnitt des Nextcloud-Protokolls im Zeitfenster der Schritte 3 und 4, mit Start- und Endzeitstempel als Kopfzeilen, darin die `cURL error 28`-Zeilen gezaehlt | `rohdaten/03-nc-protokoll-abbrueche.txt` | **Der eigentliche Beweis von DI-10-01:** zwei Zaehlungen derselben Sache, unabhaengig voneinander erhoben. `failure_kinds["EmptyResultGroup"]` der Stufe 16 gegen die Zahl aus dem Protokoll |
| 6 | **Messblock B:** Laufnummer des letzten gruenen `integration.yml`-Laufs holen (`gh run list --workflow=integration.yml --status success`), dann `FRIST=60 RUNDEN=10 CI_LAUF=<nummer> ./98b-sprachfaelle.sh` | `rohdaten/05-sprachfaelle.txt` | **Der Beweis von DI-10-02:** je Begriff eine Zeile `fremdbestand <begriff> <treffer>`, dreiwertige Urteile, Bilanzzeile mit beiden Zahlen, `ci-beleg` mit einer Laufnummer. `FRIST=60` statt der Vorgabe 360, weil die Vorgabe fuer einen erst aufzubauenden Bestand gilt |
| 7 | `aws_box.sh stop`, danach `box.env` zurueckgelesen | `rohdaten/06-kosten.txt` | Laufzeit und Kosten dieser Anfahrt, der freigegebene Deckel und die Differenz. `aws_box.sh status` meldet danach `stopped`, unabhaengig aus der API gelesen |
| 8 | Der kurze Bericht | `../README.md` | Welcher der beiden Befunde geschlossen ist und welcher nicht, jede Zahl mit ihrer Rohdatei daneben, dazu ein Abschnitt "Was diese Anfahrt nicht besser gemacht hat" |

**Zwei Vorbedingungen von Schritt 6, die vor der Anfahrt zu klaeren sind, weil
sie sonst Box-Minuten kosten:**

1. Die Laufnummer aus `integration.yml`. Ohne sie bricht `98b-sprachfaelle.sh`
   mit **22** ab, und zwar vor dem ersten Fall. Das ist Absicht: die Aussage
   dieses Laufs haengt an der Messung mit eigenem Index, und die faehrt in CI.
2. Das Passwort des Lasttest-Kontos, aus der Umgebung (`FINDLING_LOAD_PASSWORD`)
   oder aus der Datei, auf die `PWFILE` zeigt. Ohne es kann die Vorpruefung des
   Fremdbestands nicht fahren, und das Skript bricht mit **19** ab, statt wieder
   zweiwertig zu urteilen. Der Abbruch kommt vor dem Hochladen der 39 Dateien,
   kostet also nur Sekunden.

---

## 3. Die Erwartung, vorher aufgeschrieben

Dieser Abschnitt ist der Grund, warum diese Datei vor der Anfahrt entsteht. Was
hier steht, wird nach der Messung **nicht** angepasst.

| Nr | Erwartung | Woher sie kommt |
|---|---|---|
| E1 | **Stufe 16 zeigt `failures > 0`** | Am 10.09. trug das Nextcloud-Protokoll im Fenster der Stufe 16 siebzehn Abbrueche mit `cURL error 28`, waehrend das Werkzeug `"failures": 0` meldete. Der Fix zaehlt genau diese Gruppen jetzt mit |
| E2 | **Stufe 16 zeigt ein `hits_per_request` deutlich unter dem der Stufe 8** | Aus der Stufentabelle des Phase-10-Berichts, von Hand nachgerechnet: 5,25 Treffer je Anfrage auf Stufe 8 gegen 4,16 auf Stufe 16. Genau diese Rechnung nimmt der Fix dem Leser ab |
| E3 | **Stufe 8 zeigt `failures == 0`** | Die Kontrollstufe. Ein Zaehler, der auch hier Fehlschlaege meldet, zaehlt etwas anderes als das, was er zaehlen soll |
| E4 | **Die beiden Zaehlungen aus Schritt 3 und Schritt 5 stimmen ueberein**, also `failure_kinds["EmptyResultGroup"]` der Stufe 16 gleich der Zahl der `cURL error 28`-Zeilen im selben Fenster | Zwei unabhaengige Wege zu derselben Zahl. Weichen sie ab, steht die Abweichung mit einer Vermutung ueber den Grund im Bericht und wird nicht geglaettet |
| E5 | **Vier der zehn Sprachfaelle erscheinen als NICHT MESSBAR**, naemlich die Faelle 1 (`Genehmigung`), 2 (`Frist`), 4 (`Vertrag`) und 6 (`bescheid`) | Das sind genau die vier Faelle, die am 10.09. rot waren, und die Diagnose `2026-09-vergleichsmessung-m7g/rohdaten/98b-sprachfaelle-diagnose.txt` hat fuer alle vier gemessen, dass die eigene Datei nicht in die Kandidatenliste kommt: fuer drei von ihnen nicht unter den ersten 2.000, fuer `Bescheid` auf Rang 1.925 von 2.000 |
| E6 | **Moeglicherweise ein fuenfter Fall**, naemlich Fall 7, und das steht hier, bevor es eintritt | Fall 7 fragt `type:pdf bescheid`, also dasselbe Wort wie Fall 6 hinter einem Dateityp-Filter. Sein Fremdbestand ist derselbe, also faellt er sehr wahrscheinlich unter dieselbe Schwelle. Am 10.09. war er gruen, und ein gruener Fall, der jetzt NICHT MESSBAR heisst, ist kein Rueckschritt: er war gruen, obwohl der Fremdbestand ueber die Kandidatenliste entschied |
| E7 | **Die uebrigen Faelle bleiben GRUEN**, mit einem Fremdbestand von 0 daneben | `Mueller` hat im ganzen Index genau einen Treffer, und das ist die eigene Datei. Die sechs gruenen Faelle vom 10.09. sind genau die, deren Begriffe im Lastkorpus selten oder gar nicht vorkommen |
| E8 | **Die Bilanzzeile lautet `sprachfaelle bestanden 6 von 10, davon 4 nicht messbar`** (oder `5 von 10, davon 5 nicht messbar`, falls E6 eintritt) | Folgt aus E5 bis E7. Beide Zahlen in einer Zeile, weil eine Bilanz mit nur einer Zahl der Lesefehler ist, den DI-10-02 benennt |

**Eine verfehlte Erwartung ist ein Ergebnis und kein Grund fuer eine zweite
Anfahrt.** Das gilt besonders fuer E1 und E4. Die 17 Abbrueche vom 10.09. hingen
an der Kaltheit des Wirtscaches, und der ist nach dem Stillstand seit dem
10.09.2026 16:22Z anders kalt, als er es damals war. Bleibt Stufe 16 diesmal
ohne Fehlschlag, dann ist der Zaehler dadurch weder widerlegt noch belegt, und
genau dieser Satz gehoert dann in den Bericht. Eine zweite Anfahrt, um eine
Erwartung doch noch eintreten zu sehen, waere keine Messung mehr.

---

## 4. Woran der Lauf abgebrochen wird

| Bedingung | Wo sie greift | Folge |
|---|---|---|
| `occ findling:index --status` zeigt nicht 52.111 / 37 / 0 | Schritt 2, vor jeder Messung | Die Anfahrt endet, der Ist-Stand geht nach `04-bestand-vor-der-messung.txt`, der Owner entscheidet neu. Unter einem Vier-Stunden-Deckel wird kein Index neu aufgebaut |
| Mehr als eine Nextcloud am Docker-Dienst | jederzeit | Sofortiger Halt. Der Volumenname einer ExApp folgt allein aus ihrer App-Kennung (Schaden vom 07.09.) |
| `CI_LAUF` traegt keine Laufnummer | Schritt 6, vor dem ersten Fall | Rueckgabewert **22** |
| Die Vorpruefung des Fremdbestands kann nicht fahren | Schritt 6, Abschnitt 0 des Skripts | Rueckgabewert **19** |
| Nicht alle 39 Dateien hochgeladen | Schritt 6 | Rueckgabewert **15** |
| Arbeitsvorrat am Rundendeckel nicht leer | Schritt 6 | Rueckgabewert **16**. Die Faelle 8 bis 10 haengen an der OCR-Spur; dieser Block ist abbrechbar (Annahme A7) und keine Vorbedingung des Berichts |
| Mindestens ein **messbarer** Fall ist rot | Schritt 6 | Rueckgabewert **17**. Nicht messbare Faelle zaehlen hier ausdruecklich nicht mit, und das ist der ganze Unterschied zum 10.09. |
| Kein einziger Fall war messbar | Schritt 6 | Rueckgabewert **23**. Ein Lauf, in dem jeder Begriff im Fremdbestand ertrinkt, ist eine Aussage ueber die Instanz und keine ueber die Sprachkette |
| `jq` fehlt auf der Box | Schritt 6 | Rueckgabewert **18** |

Die Rueckgabewerte 15 bis 18 sind die des Originals und stehen unveraendert,
damit ein Abbruch dieses Laufs und ein Abbruch vom 10.09. dieselbe Bedeutung
haben. Neu sind allein 19, 22 und 23.

---

## 5. Nach dem Lauf

Rohdaten und Skripte committen, den kurzen Bericht in `../README.md` schreiben,
`aws_box.sh stop` (schreibt Laufzeit und Kosten selbst nach `box.env`), und die
Kosten dem Deckel gegenueberstellen. Der Abbau der Box ist ein **eigener Plan**
mit **eigener Bestaetigung** (D-03) und gehoert nicht in diese Anfahrt.

Vor dem Fertigmelden laeuft das Vokabular-Gate lokal ueber die Dateien dieses
Verzeichnisses, wie ueber jede nach aussen sichtbare Datei dieses Projekts.
