---
phase: 10-vergleichsmessung-auf-der-aws-box
plan: 05
subsystem: testing
tags: [measurement, aws-box, base-load, cold-start, tree-hash, corpus-checksum, cgroup, detached-run, watchman, mess-01]

# Dependency graph
requires:
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "40b-baumhash.sh und .py aus Welle 1 als gerufener Beweisschritt, und das Gate test_measurement_scripts.py"
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "der Digest von :dev aus Welle 2 in beiden Gestalten, und die native arm64-Feinmessung als Vergleich fuer Teil D"
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "00-ablauf.md und die Skripte 90 bis 97 aus Welle 3, mit Urteil-in-Datei-hinter-der-Pipeline"
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "96-volllauf.sh, 96b-waechter.sh, 96c-lesen.py, 96d-statusbeobachter.py und 96e-ntfy-watch.sh aus Welle 4"
  - phase: 06.1-launch-haertung
    provides: "scripts/ops/aws_box.sh mit start und stop, und die Vergleichswerte 691,8 MB, 693,4 MB und 1.812,7 MB"
provides:
  - "Die MESS-01-Kernzahl, gemessen: Grundlast im Leerlauf 103,2 MB gegen 691,8 MB und 693,4 MB, unter der gerechneten Erwartung von 118 bis 150 MB"
  - "Die erste Suche als Ereignis: anon 103,2 auf 518,2 MB, plus 415,0 MB fuer die Gewichte gegen plus 422,3 MB des Vorlaeufers"
  - "Der Kaltstart als Zahl fuer DI-07-02: 1.550,4 ms gegen die Decke von 1.500 ms, Marge minus 50,4 ms, Vorwert 1.332,1 ms"
  - "Der Baumhash-Beweis in einer NICHT leeren Rohdatei: Abbild 54 Dateien 6c47cd21..., Arbeitsbaum dasselbe, baumhash-gleich ja"
  - "Der Korpus als dieselben Bytes belegt: 50.000 Dateien, 20.208.046.426 Byte, bcbef9b2..., vor dem Indexaufbau"
  - "Die harte Grenze aus der cgroup zurueckgelesen: memory.max=2147483648"
  - "Ein abgesetzt laufender Volllauf mit Sampler, Statusbeobachter, Waechter und Meldekette, dessen Ende die Datei 00-FERTIG ist"
  - "Drei korrigierte Werkzeuge: die Laufzeitrechnung von aws_box.sh status, die Instanzzaehlung vor --rm-data, und der Sortierschluessel des Baumhashes"
  - "Der Volllauf ist durch: 52.111 Dokumente indexiert und eingebettet, 37 uebersprungen, 0 fehlgeschlagen, ohne OOM und ohne Neustart (RestartCount=0)"
  - "Die Laufzeit als Zahl: hoechstens 26 h 41 min bis zum letzten Vektor gegen 18 h 56 min in 06-11, plus 40,9 Prozent, und weiterhin eine Untergrenze"
  - "Der OOM-Beweis vor jedem Eingriff, in 96-oom-beweis.txt: oom, oom_kill und oom_group_kill je 0, max 21.939 gegen 2.796, memory.peak GLEICH memory.max"
  - "Die Aufklaerung von 52.111 gegen 51.961: die 150 Dokumente sind die Verzeichnisse neustart (30) und ocrdrei (120) aus den Haertungsdrills vom 07.09., nicht der Korpus"
  - "Die vollstaendigen Rohdaten des Laufs, von der Box geholt: 19.484 Sampler-Aufnahmen, 812 Statusaufnahmen, 325 Waechterrunden, beide Suchlastproben, der Vektorbestand"
affects: [10-06, 10-07, box-lauf]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Kostenzahl wird an den Zustand geknuepft, aus dem sie stammt: die Zeit seit dem letzten Start ist nur bei laufender Instanz eine Laufzeit"
    - "Ein Hash, der einen Stand beweisen soll, sortiert nach der Zeichenkette, die er hasht, und nie nach einem Objekt mit plattformabhaengigem Vergleich"
    - "Eine Schutzzaehlung wird gegen die echten Namen der Zielmaschine geprueft und nicht gegen die Namen der Registry, die man im Kopf hat"
    - "Eine Grundlast im Leerlauf wird auf einem Container gemessen, der beweisbar nichts tut: Arbeit abgeschaltet, Prozess neu gestartet, Poller-Durchgaenge gezaehlt und null"
    - "Der Startpunkt eines Laufs wird protokolliert, damit eine Laufzeit, die nicht bei null beginnt, als Untergrenze berichtet werden kann"

key-files:
  created:
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/89-anfahrt.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/90-bestand.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/91-korpus.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/92-wechsel.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/92-info-box.xml
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/40b-baumhash.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/93-nullstand.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/94-grundlast.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/95-spitze-vorher.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/96-volllauf-start.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/96-volllauf.csv
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/96-statusseite.jsonl
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/96b-waechter.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/99-ntfy-watch.log
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/00-FERTIG
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/96-oom-beweis.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/96-vektorbestand.txt
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/96-suchlast-nachlauf.json
    - docs/measurements/2026-09-vergleichsmessung-m7g/rohdaten/96-suchlast-danach.json
  modified:
    - scripts/ops/aws_box.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/90-bestand.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/92-wechsel.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/40b-baumhash.py
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md
    - backend/tests/test_ops_scripts.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Der Baumhash sortiert nach dem relativen posix-Pfad und nicht nach dem Path-Objekt. Die Windows-Variante faltet Gross- und Kleinschreibung, die posix-Variante nicht, also ergab derselbe Baum 26b55908... auf Windows und 4a4c6f62... auf der Box, bei 58 byteweise identischen Dateien. Der Beweis, dass Abbild und Arbeitsbaum derselbe Stand sind, haing damit an der Maschine, die ihn ausrechnet. Keine berichtete Vergleichszahl wird retiriert: das Python-Paket ergibt 6c47cd21... unter beiden Sortierschluesseln auf beiden Plattformen"
  - "aws_box.sh status nennt die Zeit seit dem letzten Start nur bei laufender Instanz eine Laufzeit. Eine angehaltene Instanz antwortet weiter mit ihrer LaunchTime, also zaehlte die Rechnung jede Parkstunde als Laufstunde: 52,3 Stunden und 5,80 USD fuer eine Box, die 1,95 Stunden gelaufen war. An dieser Zahl haengt der Kostendeckel des Owners"
  - "Die Instanzzaehlung vor --rm-data haengt am Repositoriumsnamen und nicht an einem Registry-Pfad. Die gefaehrliche Richtung war nicht der Abbruch bei 0, sondern dass das alte Muster MIT der zweiten, handgebauten Nextcloud vom 07.09. genau 1 gezaehlt und den zerstoerenden Befehl durchgelassen haette"
  - "Die Grundlast wird auf einem Container gemessen, der beweisbar nichts tut. Schritt 4 fuellt die Warteschlange und der Poller beginnt sofort zu arbeiten, weil Schritt 3 die PHP-App einschaltet; also ist die App fuer Schritt 5 wieder abgeschaltet und der Container neu gestartet worden, damit 'Modell nie geladen, noch keine Suche' auch stimmt. Die Zahl der Poller-Durchgaenge steht als Beleg daneben: null"
  - "Der Preis dieser Reihenfolge steht im Ablaufplan und nicht in einer Fussnote: beim Anstoss lagen 1.653 Dateien schon im Index, also ist die gemessene Laufzeit eine Untergrenze und wird als eine berichtet"
  - "Der /etc/hosts-Pin ist Rueckfall 1 und nicht curl --resolve. Er erreicht dasselbe, naemlich dass nichts auf den alten A-Record laeuft, und er kostet keine Aenderung an sieben Messskripten mitten im Lauf. Der Preis steht im Protokoll: ueberlebt der Lauf einen Maschinenneustart nicht, ist der Pin erneut stumpf"
  - "digest-gleich nein ist ein benannter Befund und kein Abbruch, genau wie das Skript es vorsieht: :dev ist ein wandernder Zeiger, der Pfadfilter von docker.yml reicht in backend/**, und der Vergleich, der traegt, ist der Baumhash"
  - "MESS-01 bis MESS-03 bleiben Pending. Der Bericht existiert nicht, und abhaken darf sie der Plan, der die Zahlen zusammentraegt"
  - "Die Laufzeit wird gegen die vergleichbare Groesse gestellt und nicht gegen die bequeme: 06-11 nennt 18 h 56 min BIS ZUM LETZTEN VEKTOR, also steht dort hoechstens 26 h 41 min und nicht die 27,0 Stunden aus 00-FERTIG, die 25 Minuten Stillestandsbestaetigung des Waechters enthalten. Beide Zahlen stehen im Bericht, jede mit ihrer Definition"
  - "Der Mehrbestand von 150 Dokumenten wird an seinen Verzeichnissen belegt und nicht an den Verdikten vermutet: neustart (30 Dateien, 07.09. 05:59) und ocrdrei (120 Dateien, 07.09. 05:46) liegen im Baum des indexierten Nutzers und sind nach dem Lauf vom 05.09. entstanden. 52.111 minus 150 ist 51.961 auf das Dokument genau, und uebersprungen sind in beiden Laeufen exakt 37"
  - "Der Durchsatz ist ueber den ganzen Lauf STABIL bei 32 bis 34 Dokumenten je Minute geblieben. Das schliesst eine schleichende Verschlechterung durch den Speicherdruck als Erklaerung fuer die Mehrlaufzeit aus und verschiebt die Frage auf den Zulauf: in 62 von 325 Lesungen war der Arbeitsvorrat null"
  - "Der Uebergangswert der Suchlast ist eine Fehlstelle und wird als eine berichtet. Die Schwelle des Waechters ist embedded groesser 200, und beim Anstoss standen bereits 264 Vektoren, also fiel die Probe in Runde 1 bei 1.679 Dokumenten statt am Uebergang der Spuren. Dieselbe Wurzel wie der Untergrenzen-Vorbehalt"

patterns-established:
  - "Eine Zahl, an der ein Kostendeckel haengt, wird gegen den Zustand geprueft, aus dem sie stammt"
  - "Ein plattformabhaengiger Vergleich in einem Beweisschritt ist ein Fehler, auch wenn er auf der Maschine des Entwicklers stimmt"
  - "Eine Leerlaufmessung fuehrt den Beleg mit, dass Leerlauf war"

requirements-completed: []
requirements-touched: [MESS-01, MESS-02]

# Metrics
duration: 1h20m Sitzungszeit, davon 27 h 06 min unbeaufsichtigter Lauf dazwischen
completed: 2026-09-10
---

# Phase 10 Plan 05: Die Anfahrt, die Zahlen vor dem Volllauf und der abgesetzte Anstoss Summary

**Die Grundlast im Leerlauf ist von 691,8 MB auf 103,2 MB gefallen, gemessen auf einem Container, der beweisbar nichts tat, und der Volllauf ist durch: 52.111 Dokumente ohne OOM und ohne Neustart, in hoechstens 26 h 41 min gegen 18 h 56 min, also 40,9 Prozent langsamer als der Vorlaeufer und ueber der Owner-Erwartung von 22 bis 26 Stunden.**

## Performance

- **Duration:** 55 min fuer die Tasks 1 bis 3 am 09.09., 25 min fuer Task 4 am 10.09., dazwischen 27 h 06 min unbeaufsichtigter Lauf
- **Started:** 2026-09-09T09:15:00Z
- **Tasks 1 bis 3 fertig:** 2026-09-09T10:10:00Z
- **Anstoss des Volllaufs:** 2026-09-09T09:58:42Z
- **Ende des Volllaufs:** 2026-09-10T13:05:11Z (`00-FERTIG`)
- **Completed:** 2026-09-10T13:40:00Z
- **Tasks:** 4 von 4, Task 4 war ein blockierender Checkpoint ueber die Laufzeit und ist mit dem Resume-Signal beantwortet
- **Box-Minuten:** 51 bis zum Anstoss, dann 27 h 06 min Lauf; Stand nach Task 4 **27,9 h** von 30 h Deckel
- **Kosten:** **3,23 USD** netto von 3,50 USD Deckel (`aws_box.sh status`, 2026-09-10T13:14Z)

## Accomplishments

- **Die MESS-01-Kernzahl ist gemessen und sie ist der Befund, auf den die Phase hinauslief:** Grundlast im Leerlauf **103,2 MB** (`anon` 108.199.936 Byte) gegen **691,8 MB** aus 06-11 und **693,4 MB** aus der Nachmessung. Das sind 588,6 MB weniger, und es ist besser als die gerechnete Erwartung von 118 bis 150 MB. Der Beleg, dass Leerlauf war, steht daneben: null Poller-Durchgaenge seit dem Containerstart, Modell nie geladen, keine Suche. Der Stoerfaktor ist ausgeschlossen, weil dieser Start dieselbe Wortliste liest und denselben Automaten baut wie die Vorlaeufer (276.496 Eintraege, im Protokoll).
- **Die erste Suche als Ereignis, und sie bestaetigt die Deutung:** `anon` 103,2 auf 518,2 MB, also **plus 415,0 MB** fuer die ankommenden Gewichte, gegen plus 422,3 MB des Vorlaeufers. Dieselben Gewichte, dieselbe Bewegung, nur die Grundlast darunter ist weg.
- **Der Beweisschritt, den beide Vorlaeuferberichte LEER gelassen haben, ist nicht leer:** `40b-baumhash.txt` traegt drei `baumhash:`-Zeilen und ein Urteil. Abbild 54 Dateien `6c47cd21...`, Arbeitsbaum dieselben 54 und derselbe Hash, `baumhash-gleich ja`. Kriterium 1 ist damit belegt statt behauptet.
- **Der Korpus ist als dieselben Bytes belegt, vor dem Indexaufbau:** `korpus-gleich ja`, 50.000 Dateien, 20.208.046.426 Byte, `bcbef9b2...`, die arm64-Zeile. Annahme A3 ist gemessen und nicht uebernommen, und der Vergleich lief gegen die richtige der beiden Pruefsummen.
- **Die harte Grenze steht bei 2 GiB, aus der cgroup zurueckgelesen** und nicht aus dem Docker-Klienten: `memory.max=2147483648`, `memory.swap.max=0`, nach der Registrierung neu gesetzt, weil ein Register sie wegwirft.
- **Der Volllauf laeuft abgesetzt und kann nachts allein zu Ende kommen.** Anstoss 09:58:42Z, Gegenprobe nach 361 s mit `arbeitsvorrat-da ja`, 47 gezaehlte Poller-Durchgaenge als DI-05-36-Beweis. Sampler mit 5 s und vier Aufnahmen VOR dem Anstoss, Statusbeobachter mit 120 s, Waechter mit Rundendeckel 340, Meldekette mit `http=200`.
- **Die Trockenprobe des Lesers steht mit ihrer Ausgabe im Protokoll und trifft eine echte Aufnahme:** `2040 1653 264`. Vorrat, `indexed` und `embedded` aus `backend`, nicht die Null der obersten Ebene. Fallstrick 8, der teuerste Fehler beider Vorlaeufer, ist damit auf dieser Maschine geschlossen und nicht nur im Gate.
- **Drei Werkzeuge sind korrigiert, alle drei mit einer Zusicherung daneben, und eines davon hatte CI seit Welle 1 rot.** Die Einzelheiten stehen unter Deviations, weil jede der drei eine Zahl betraf, die falsch war und richtig aussah.
- **Der Lauf ist durch, allein, ueber Nacht, und sein Ende war die Datei, die es sein sollte.** 52.111 Dokumente indexiert und eingebettet, 37 uebersprungen, 0 fehlgeschlagen, `OOMKilled=false`, `RestartCount=0`, `oom`, `oom_kill` und `oom_group_kill` je **0**. Der Waechter hat in Runde 325 von 340 abgeschaltet, also aus eigenem Urteil und nicht am Rundendeckel. Die sechs Antworten des Checkpoints stehen unten in einem eigenen Abschnitt.
- **Und der Lauf hat laenger gebraucht, als er sollte, und das ist der zweite Befund dieses Plans.** Hoechstens **26 h 41 min** bis zum letzten Vektor gegen **18 h 56 min** in 06-11, also plus 40,9 Prozent, bei einem Mehrbestand von nur 0,29 Prozent. Er liegt damit ueber der Owner-Erwartung von 22 bis 26 Stunden, und der Untergrenzen-Vorbehalt zieht in dieselbe Richtung: 1.653 Dateien waren beim Anstoss schon indexiert, ein Lauf von null haette also noch laenger gebraucht.

## Task Commits

1. **Task 1: Owner-Checkpoint** , kein Commit. Die Freigabe ist in `89-anfahrt.txt` woertlich protokolliert.
2. **Task 2, Korrektur 1: die Laufzeitrechnung von `status`** , `5a1356f` (fix)
3. **Task 2, Korrektur 2: die Instanzzaehlung vor `--rm-data`** , `6532015` (fix)
4. **Task 2, Korrektur 3: der Sortierschluessel des Baumhashes** , `7f121f3` (fix)
5. **Task 2: die Rohdaten vor dem Volllauf, Bestand bis erste Suche** , `e3ec58b` (feat)
6. **Task 2: das Protokoll der Anfahrt** , `2a37a60` (docs)
7. **Task 3: der Volllauf laeuft abgesetzt** , `0bbfd9f` (feat)
8. **Tasks 1 bis 3: die Metadaten** , `0dd007d` (docs)
9. **Task 4: die Rohdaten des fertigen Laufs, von der Box geholt** , `5d276dd` (feat)
10. **Task 4: die sechs Antworten des Checkpoints** , dieser Metadaten-Commit (docs)

## Die Zahlen, die dieser Plan erzeugt hat

| Groesse | Gemessen 09.09. | Vorwert | Quelle |
|---|---|---|---|
| Grundlast im Leerlauf, `anon` | **103,2 MB** | 691,8 MB (06-11), 693,4 MB (Nachmessung) | `94-grundlast.txt` |
| Erwartung fuer die Grundlast | , | 118 bis 150 MB gerechnet | unterboten |
| Erste Suche, `anon` davor auf danach | 103,2 auf 518,2 MB, plus 415,0 MB | 694,3 auf 1.116,6 MB, plus 422,3 MB | `95-spitze-vorher.txt` |
| Kaltstart, eine Anfrage | **1.550,4 ms** | 1.332,1 ms (Plan 07-01) | `95-spitze-vorher.txt` |
| Decke `ExAppService::REQUEST_TIMEOUT_SECONDS` | 1.500,0 ms, Marge **minus 50,4 ms** | Marge plus 167,9 ms | dieselbe Datei |
| Korpus | 50.000 Dateien, 20.208.046.426 Byte, `bcbef9b2...` | identisch | `91-korpus.txt` |
| Baumhash Abbild und Arbeitsbaum | 54 Dateien, `6c47cd21...`, gleich | identisch | `40b-baumhash.txt` |
| Baumhash php | 58 Dateien, `4a4c6f62...` | `26b55908...` war das Windows-Artefakt | `40b-baumhash.txt` |
| Digest von `:dev` | `sha256:78ab61d8...` | `eed6a5fc...` / `ae58d930...` | benannter Befund |
| Harte Grenze | `memory.max=2147483648` | Erwartungswert getroffen | `92-wechsel.txt` |
| `memory.events`, Ende des Laufs | `oom`, `oom_kill`, `oom_group_kill`, `low`, `high` je **0**; **`max` 21.939** | `max` 2.796 in 06-11, 0 in der Nachmessung | `96-oom-beweis.txt` |
| `memory.peak`, Ende des Laufs | **2.147,5 MB, gleich der harten Grenze** | 1.837,8 MB (06-11), 1.812,7 MB (Nachmessung) | `96-oom-beweis.txt` |
| Hoechster `anon` des ganzen Laufs | **1.764,2 MB** (1.849.946.112 Byte) | 1.837,8 MB (06-11), 1.812,7 MB (Nachmessung) | `96-volllauf.csv`, Summenzeile |
| Laufzeit bis zum letzten Vektor | **hoechstens 26 h 41 min**, Untergrenze | 18 h 56 min (06-11) | `96b-waechter.log`, `00-FERTIG` |
| Durchsatz ueber den ganzen Lauf | **31,5 Dokumente je Minute**, stabil 32 bis 34 im Mittelteil | 45,7 je Minute gerechnet, 43 je Minute berichtet | `96b-waechter.log` |
| Indexiert / uebersprungen / fehlgeschlagen | **52.111 / 37 / 0** | 51.961 / 37 / 0 | `96-vektorbestand.txt` |
| Suchlast bei vollem Bestand, p95 (10 Anfragen) | **830,6 ms** | 524,0 ms | `96-suchlast-danach.json` |

**Was diese Tabelle noch nicht sagt:** die Spitzen getrennt nach Phase, die Nebenlaeufigkeitsreihe, der Endungsvergleich und der Kaltstart auf vollem Bestand entstehen erst in Plan 10-06. Was der Lauf selbst erzeugt hat, steht im naechsten Abschnitt.

**Und ein Vorbehalt, der zur Laufzeit gehoert:** beim Anstoss lagen bereits 1.653 der 50.000 Dateien im Index. Die gemessene Laufzeit ist deshalb eine **Untergrenze**, das Skript sagt es selbst in `startpunkt-bewertung`, und `00-ablauf.md` traegt den Grund. Der Vorbehalt zieht in die unangenehme Richtung: ein Lauf von null haette laenger gedauert als die gemessenen 26 h 41 min, nicht kuerzer.

## Task 4: Der Lauf ist durch, die sechs Antworten des Checkpoints

Resume-Signal am 2026-09-10, Wortlaut "lauf ist durch, weiter". **Auf der Box ist in der Zwischenzeit nichts angefasst worden und in diesem Task auch nicht:** der Container laeuft seit `2026-09-09T09:40:51Z` ohne Neustart (`RestartCount=0`, `Status=running`), gelesen wurde ausschliesslich mit `cat`, `tail`, `ls`, `find` und `awk`, dazu `aws_box.sh status` von diesem Rechner. Kein `occ`, kein `docker exec`, kein `docker restart`, kein `stop`. Alle vier abgesetzten Beobachter sind von selbst zu Ende gegangen; `pgrep` findet keinen mehr.

### 1. `00-FERTIG` existiert, und die Laufzeit steht neben 18 h 56 min

Die Datei, woertlich, wie der Waechter sie geschrieben hat:

```
volllauf-fertig 2026-09-10T13:05:11Z
stunden=27.0
ende-erkannt ja
oom-beweis=/home/ubuntu/work/repo0918/docs/measurements/2026-09-vergleichsmessung-m7g/skripte/../rohdaten/96-oom-beweis.txt
weckwort: volllauf pruefen
```

Anstoss war `2026-09-09T09:58:42Z`. Daraus vier Marken, und es ist wichtig, welche davon neben 18 h 56 min steht:

| Marke | Zeitpunkt | Nach dem Anstoss | Quelle |
|---|---|---|---|
| Letzte Runde mit Arbeit im Vorrat (Runde 319, `vorrat=31`) | 2026-09-10T12:34:57Z | 26 h 36 min 15 s | `96b-waechter.log` |
| **Erste Runde mit `vorrat=0` und `indexed=embedded=52111` (Runde 320)** | **2026-09-10T12:39:57Z** | **26 h 41 min 15 s** | `96b-waechter.log` |
| Ende beider Spuren erkannt, nach fuenf stillen Runden | 2026-09-10T13:04:57Z | 27 h 06 min 15 s | `96b-waechter.log` |
| `00-FERTIG` geschrieben | 2026-09-10T13:05:11Z | 27 h 06 min 29 s | `00-FERTIG` |

**Die vergleichbare Zahl ist hoechstens 26 h 41 min.** 06-11 nennt "18 h 56 min bis zum letzten Vektor", und der letzte Vektor dieses Laufs fiel zwischen 12:34:57Z und 12:39:57Z. Die `stunden=27.0` aus `00-FERTIG` enthalten zusaetzlich die 25 Minuten, die der Waechter braucht, um die Stille zu bestaetigen; sie sind die richtige Zahl fuer die Sitzungsplanung und die falsche fuer den Vergleich. Beide stehen hier mit ihrer Definition.

**Die Einordnung, ehrlich:** 26 h 41 min gegen 18 h 56 min sind **plus 40,9 Prozent**. Die Owner-Freigabe vom 09.09. nennt woertlich "22 bis 26 Stunden abgesetzt ueber Nacht mit Meldekette ist gewollt" (`89-anfahrt.txt`), der Plan selbst rechnete mit rund 19 Stunden. Der Lauf liegt **ueber** beidem: 41 Minuten ueber der oberen Kante der Owner-Erwartung, gemessen an der vergleichbaren Marke, und 1 h 06 min ueber ihr, gemessen an `00-FERTIG`. Der Methodikvermerk aus `00-ablauf.md` macht es nicht besser, sondern schlechter: beim Anstoss lagen 1.653 der Dateien schon im Index und 264 Vektoren schon im Bestand, also hat der Lauf **weniger** Arbeit getan als ein Lauf von null und trotzdem laenger gebraucht. Die berichtete Laufzeit bleibt eine Untergrenze.

**Was die Mehrlaufzeit NICHT erklaert:** der Mehrbestand. 52.111 gegen 51.961 sind plus 0,29 Prozent gegen plus 40,9 Prozent Laufzeit.

**Was als Erklaerung in Frage kommt, und was die Rohdaten dazu schon sagen:**

- **Der Durchsatz war ueber den ganzen Lauf stabil**, nicht abfallend. In 40-Runden-Bloecken zu je 200 Minuten: 27,5 / 34,1 / 33,1 / 32,7 / 32,5 / 34,6 / 32,7 / 25,6 Dokumente je Minute. Der erste Block ist der Anlauf, der letzte laeuft leer. Dazwischen liegt eine Gerade. **Das schliesst eine schleichende Verschlechterung als Erklaerung aus**, also insbesondere den Speicherdruck. Ueber alles: 50.458 Dokumente in 1.601 Minuten, **31,5 je Minute**, gegen 45,7 je Minute in 06-11 (51.961 in 1.136 Minuten).
- **Der Zulauf hat gestockt.** In **62 von 325 Lesungen (19,1 Prozent)** stand `vorrat=0`, der Poller hatte also nichts zu tun und wartete auf den Fuenf-Minuten-Cron der Nextcloud-Haelfte, der in Schueben von bis zu 500 einreiht (`vorrat` pendelt zwischen 0 und 500). Eine Momentaufnahme je Runde beweist keine Leerlaufzeit, aber sie ist der einzige Kandidat, den die Daten dieses Plans stuetzen.
- **Die Spuren liefen gekoppelt statt nacheinander.** In 06-11 war die erste Spur nach 18 h 04 min durch und ein Nachlauf von 52 Minuten holte die Einbettung nach. Hier hat die Einbettung ab Runde 20 zur Indexierung aufgeschlossen und ist bis zum Ende hoechstens einige hundert Dokumente zurueckgeblieben (Runde 314: `indexed=51716 embedded=51714`). Eine Phasengrenze "Uebergang der Spuren" gibt es in diesem Lauf nicht.

Die Ursachenanalyse gehoert nicht hierher. Sie braucht `rss_digest.py` mit Phasengrenzen aus der Statusreihe und die Verdiktverteilung, und beides steht in Plan 10-06 Task 1. **Hier steht die Zahl, und sie steht ungeschoent.**

### 2. Das Waechterprotokoll, und der Nebenbefund 52.111 gegen 51.961

Der Waechter hat **325 Lesungen** gemacht und ist aus eigenem Urteil abgeschaltet, nicht am Deckel. Die letzten sechs Zeilen:

```
waechter runde=320 vorrat=0 indexed=52111 embedded=52111 gesehen=1 still=0 leer=0 2026-09-10T12:39:57Z
waechter runde=321 vorrat=0 indexed=52111 embedded=52111 gesehen=1 still=1 leer=0 2026-09-10T12:44:57Z
waechter runde=322 vorrat=0 indexed=52111 embedded=52111 gesehen=1 still=2 leer=0 2026-09-10T12:49:57Z
waechter runde=323 vorrat=0 indexed=52111 embedded=52111 gesehen=1 still=3 leer=1 2026-09-10T12:54:57Z
waechter runde=324 vorrat=0 indexed=52111 embedded=52111 gesehen=1 still=4 leer=2 2026-09-10T12:59:57Z
waechter runde=325 vorrat=0 indexed=52111 embedded=52111 gesehen=1 still=5 leer=3 2026-09-10T13:04:57Z
```

`ende-erkannt ja`, `lesungen 325`, danach `waechter-ende`. Kein `unklar` in einer einzigen Lesung, also hat Fallstrick 8 diesen Lauf nicht angefasst: `embedded` stand nie ueber viele Runden exakt gleich, ausser in den fuenf Stillerunden, fuer die genau das der Zweck ist.

**Der Nebenbefund, und er ist aufgeklaert.** Erwartet waren 51.961 indexierte Dokumente aus 06-11, gemessen wurden **52.111**, also plus 150. Die Differenz liegt nicht an den Verdikten und nicht am Korpus, sondern an zwei Verzeichnissen, die es am 05.09. noch nicht gab:

| Verzeichnis im Baum des indexierten Nutzers | Dateien | Angelegt |
|---|---|---|
| `loadtest` (der Messkorpus) | 50.000 | 2026-09-04 17:21 |
| `drill` | 1.500 | 2026-09-05 08:08 |
| `workersA` | 200 | 2026-09-05 08:53 |
| `workersB` | 200 | 2026-09-05 09:09 |
| `Templates`, `Photos`, `Documents` und sechs Dateien der Nextcloud-Skelettvorlage | 64 | 2026-09-05 07:58 |
| **`ocrdrei`** | **120** | **2026-09-07 05:46** |
| **`neustart`** | **30** | **2026-09-07 05:59** |
| Summe auf der Platte | **52.114** | |

`ocrdrei` und `neustart` sind die beiden Drills der Haertungsphase vom **07.09.**, also zwei Tage NACH dem Lauf vom 05.09. und zwei Tage VOR diesem. Sie liegen im `files`-Baum des Nutzers `lasttest`, also reiht `findling:index --restart` sie mit ein. **30 plus 120 sind 150, und 52.111 minus 150 sind 51.961 auf das Dokument genau.**

Drei Gegenproben, die die Deutung tragen:

- Der **Korpus selbst ist byteweise derselbe**: `korpus-gleich ja`, 50.000 Dateien, 20.208.046.426 Byte, `bcbef9b2...`, gemessen VOR dem Indexaufbau (`91-korpus.txt`). Am Messgegenstand hat sich nichts geaendert.
- **Uebersprungen wurden in beiden Laeufen exakt 37** (`96-vektorbestand.txt`, gelesen aus `state.db` des Backends). Waere die Differenz eine Verschiebung in den Verdikten, muesste diese Zahl sich bewegen. Sie tut es nicht: die 150 zusaetzlichen Dateien sind samt und sonders indexierbar, und keine bisher indexierbare Datei ist es geworden oder gewesen.
- **Fehlgeschlagen: 0**, wie in 06-11.

Ein Rest bleibt und wird als Rest benannt: die Verdikte zaehlen zusammen 52.148 (52.111 plus 37), der Dateizaehler auf der Platte 52.114, also ein Versatz von **plus 34**. Derselbe Versatz steckt in 06-11: dort stehen 51.998 Verdikte gegen 51.964 Dateien, die es am 05.09. gab. **Der Versatz ist in beiden Laeufen identisch und hebt sich im Vergleich auf.** Woher er kommt, laesst sich nur aus dem Dateicache oder aus `state.db` beantworten, und beides braucht Zugriffe, die dieser Task sich versagt. Es ist genau die Frage, fuer die Plan 10-06 Task 1 den Endungsvergleich und die Verdiktverteilung vorsieht; dort ist sie zu klaeren.

### 3. Der Rundendeckel-Abbruch: trifft nicht zu

**Punkt 3 des Checkpoints ist gegenstandslos.** Der Waechter ist in Runde **325 von 340** aus eigenem Urteil abgeschaltet, mit `ende-erkannt ja` und `lauf-ende-erkannt 2026-09-10T13:04:57Z`. Der Abbruchpfad aus dem Ablaufplan, Rueckgabewert 13 am Rundendeckel, ist nicht gegangen worden. Es gibt keine Teilzahlen, es gibt kein Nachfassen zu entscheiden, und der Lauf wird im Bericht als **vollstaendig** gefuehrt. Reserve am Ende: 15 Runden, also 1 Stunde 15 Minuten.

### 4. Der Kostendeckel ist eingehalten, aber er ist fast aufgebraucht

`aws_box.sh status`, abgefragt 2026-09-10T13:14Z, mit der in diesem Plan korrigierten Laufzeitrechnung (`5a1356f`):

```
instance  i-06b1d913f5c6f669b m7g.large running in eu-central-1c
address   3.69.147.2
running   27.9 hours since 2026-09-09T09:19:50+00:00
rate      0.097800 USD per hour for the box, 0.013041 for 100 GB of storage, 0.005000 for the address
spent     3.23 USD so far, net, from the pinned public rates
```

| Groesse | Stand | Deckel | Rest |
|---|---|---|---|
| Laufzeit der Box | **27,9 h** | 30 h | **2,1 h** |
| Kosten netto | **3,23 USD** | 3,50 USD | 0,27 USD, also 2,3 h |

**Beide Deckel sind eingehalten, und beide sind fast erreicht.** Der bindende ist die Laufzeit: bei 0,115841 USD je Stunde ist die 30-Stunden-Marke am **2026-09-10T15:19:50Z** erreicht, das Geld reicht 14 Minuten laenger. Die Vorhersage aus dem Checkpoint (rund 27 bis 28 Stunden, rund 3,15 USD) ist getroffen; was sie nicht vorhergesehen hat, ist, dass der Lauf sieben Stunden mehr davon verbraucht als geplant und damit fast die ganze Reserve.

**Das ist der Punkt, der in Plan 10-06 als Erstes auf den Tisch gehoert**, und er steht unten unter "Next Phase Readiness" noch einmal als Owner-Entscheid.

### 5. Die Meldekette hat gemeldet, viermal, jedes Mal mit 200

`99-ntfy-watch.log` vollstaendig, mit dem HTTP-Code jedes Versuchs:

| Zeitpunkt | Versuch | HTTP | Prioritaet |
|---|---|---|---|
| 2026-09-09T10:04:43Z | `meldekette scharf, modus=start` | , | , |
| 2026-09-09T10:04:43Z | `meldekette scharf, modus=warten, prueft alle 300 s, deckel 20 h` | , | , |
| 2026-09-09T10:04:43Z | Titel "Findling 10-04 Volllauf gestartet" | **200** | default |
| 2026-09-10T06:04:44Z | Titel "Findling 10-04 Volllauf ueber 20 h" | **200** | high |
| 2026-09-10T06:04:44Z | `DECKEL 20h ueberschritten` | , | , |
| 2026-09-10T13:05:11Z | Titel "Findling 10-04 Volllauf fertig", aus dem Waechter (`modus=senden`) | **200** | default |
| 2026-09-10T13:09:44Z | `00-FERTIG gesehen nach 27.1h`, aus der wartenden Haelfte | , | , |
| 2026-09-10T13:09:45Z | Titel "Findling 10-04 Volllauf fertig", zum zweiten Mal | **200** | default |

**Vier Versuche, vier Mal 200, kein 403 und kein stiller Ausfall.** Der 403 vom 05.09. ist nicht wiedergekehrt; er kam von der damals neuen oeffentlichen Adresse, und diese Box faehrt seit dem 09.09. auf `3.69.147.2` mit dem gezogenen A-Record.

Zwei Beobachtungen, die dazugehoeren:

- **Die Fertigmeldung kam doppelt**, um 13:05:11Z aus dem Waechter und um 13:09:45Z aus der wartenden Haelfte, die `00-FERTIG` selbst gesehen hat. Beide Wege funktionieren also unabhaengig voneinander, und das ist der Grund, warum der Doppelversand hier als Redundanz und nicht als Fehler berichtet wird. Fuer einen naechsten Lauf waere ein Riegel trotzdem billig.
- **Der Vertrag hat trotzdem gehalten, was er sollte.** Massgeblich war `00-FERTIG`, nicht die Nachricht. Dass die Nachricht diesmal ankam, ist ein erfreulicher Nebenbefund und kein Ersatz fuer die Datei.

### 6. Die Box laeuft, der Container ist unangetastet, der OOM-Beweis liegt

`aws_box.sh stop` ist **nicht** gefahren worden und steht in Plan 10-06 nach der Owner-Abnahme. Der Beleg, dass nichts angefasst wurde, steht in `96-oom-beweis.txt` und ist zweimal erhoben, einmal am Ende beider Spuren vor jedem Eingriff und einmal am Ende des Waechters:

| Zaehler | `ende-beider-spuren-vor-jedem-eingriff` (13:04:57Z) | `ende-des-waechters` (13:05:11Z) | 06-11 |
|---|---|---|---|
| `low` / `high` | 0 / 0 | 0 / 0 | , |
| **`max`** | **21.939** | 21.939 | **2.796** |
| **`oom`** | **0** | 0 | 0 |
| **`oom_kill`** | **0** | 0 | 0 |
| **`oom_group_kill`** | **0** | 0 | 0 |
| `sock_throttled` | 1.997 | 1.997 | , |
| `memory.max` | 2.147.483.648 | 2.147.483.648 | dieselbe Grenze |
| **`memory.peak`** | **2.147.483.648** | 2.147.483.648 | 1.837,8 MB (anon) |
| `memory.current` | 1.762.979.840 | 1.837.355.008 | , |
| `OOMKilled` | **false** | false | false |
| `RestartCount` | **0** | 0 | 0 |

`memory.events.local` traegt dieselben sieben Zahlen wie `memory.events`, also stammt der ganze Druck aus dieser cgroup und nicht aus einer Kindgruppe.

**Zwei Zahlen dieser Tabelle sind ein Befund und keine Formalie**, und beide gehen in Plan 10-06 und in den Bericht:

- **`memory.peak` ist GLEICH `memory.max`.** Der Container hat die harte Grenze von 2 GiB erreicht, zum ersten Mal am **2026-09-09T14:59:28Z**, also **5 Stunden nach dem Anstoss**, und ist danach dort geblieben. Der Vorlaeufer blieb mit 1.837,8 MB darunter. Erreicht heisst nicht ueberschritten: es ist kein Byte OOM gegangen.
- **`max` steht auf 21.939 gegen 2.796**, also das 7,8-Fache an Reclaim-Ereignissen. Der Ablaufplan hatte hier ausdruecklich die **Null** erwartet ("Die Null bei `max` ist der eigentliche Gewinn dieser Messung"). Die Null ist nicht eingetreten, und die Erwartung wird nicht nachtraeglich umgeschrieben.

Der Grund liegt sichtbar neben den Zahlen: **`anon` ist gefallen, der Seitencache ist gestiegen.** Hoechster `anon` des ganzen Laufs **1.764,2 MB** (1.849.946.112 Byte) gegen 1.837,8 MB in 06-11 und 1.812,7 MB in der Nachmessung, also 73,6 MB weniger Heap. Was die Grenze fuellt, ist `file`: 154,1 MB am Ende des Laufs und 226,8 MB waehrend der letzten Suchlast, gegen 47,8 MB am Anfang. Der Tantivy-Index ist auf 786,5 MB gewachsen, und dessen Seitencache liegt in derselben cgroup. Ob das die Mehrlaufzeit erklaert, sagt der stabile Durchsatz aus Punkt 1 eher nicht; die Auswertung mit Phasengrenzen steht in 10-06.

**Was der Waechter sonst noch mitgebracht hat und was in 10-06 gehoert** (hier nur benannt, nicht ausgewertet):

| Groesse | Gemessen | Vorwert 06-11 | Quelle |
|---|---|---|---|
| Chunks | 146.171 | 145.854 | `96-vektorbestand.txt` |
| Dokumente mit Vektor | 52.111 | 51.961 | dieselbe Datei |
| Chunks je Dokument | 2,805 | 2,807 | dieselbe Datei |
| Byte je Dokument | 1.318,3 | 1.321,0 | dieselbe Datei |
| `vectors.db` plus WAL | 64,1 MB plus 4,6 MB | , | dieselbe Datei |
| Tantivy-Verzeichnis | 786,5 MB | , | dieselbe Datei |
| Vektoranteil am Tantivy-Index | 8,73 Prozent | 8,74 Prozent | dieselbe Datei |
| Suchlast bei vollem Bestand, p50 / p95 | 408,7 / **830,6** ms | 524,0 ms p95 | `96-suchlast-danach.json` |
| Suchlast am "Uebergang", p50 / p95 | 357,7 / 409,9 ms | 1.129,0 ms p95 im Nachlauf | `96-suchlast-nachlauf.json` |

**Und eine Fehlstelle, die hier benannt gehoert, weil 10-06 sonst einen Vergleich zieht, den es nicht gibt.** Die Suchlastprobe "am Uebergang der Spuren" ist **nicht am Uebergang gefahren worden, sondern in Runde 1**, um 10:04:44Z, bei 1.679 indexierten Dokumenten. Die Schwelle des Waechters ist `embedded` groesser 200 (`SCHWELLE=200` in `96b-waechter.sh`), und beim Anstoss standen bereits **264** Vektoren im Bestand, also war die Schwelle vor der ersten Runde ueberschritten. Das ist dieselbe Wurzel wie der Untergrenzen-Vorbehalt der Laufzeit: der Lauf begann nicht bei null. Die 409,9 ms sind deshalb **kein** Gegenstueck zu den 1.129,0 ms aus dem Nachlauf von 06-11, sondern eine p95-Messung auf fast leerem Bestand, und sie werden im Bericht als Fehlstelle gefuehrt. Das Gegenstueck, das traegt, ist die Probe am Ende: **830,6 ms p95 bei vollem Bestand gegen 524,0 ms**, gemessen bei Nebenlaeufigkeit 1 mit zehn Anfragen, also mit der duennen Reihe. Die belastbare p95-Reihe mit 410 Anfragen ueber fuenf Stufen ist Plan 10-06 Task 1.

## Decisions Made

Die tragenden Entscheidungen stehen im Frontmatter. Drei verdienen den Fliesstext.

**Warum ein Baumhash nicht nach Path-Objekten sortieren darf.** `40b-baumhash.py` hat `sorted(root.glob(pattern))` geschrieben, also Path-Objekte verglichen. Deren Vergleich ist plattformabhaengig: die Windows-Variante faltet Gross- und Kleinschreibung, die posix-Variante nicht. Auf Windows stand damit `tests/bootstrap.php` vor `tests/Unit/...`, auf der Box umgekehrt, und derselbe Baum ergab zwei Hashes. Der eigene Docstring des Rezepts schreibt die Sortierung nach dem relativen posix-Pfad seit immer vor, die Zeile tat es nicht. Das ist kein Schoenheitsfehler: der Baumhash ist der einzige Beweis, dass Abbild und Arbeitsbaum derselbe Stand sind, und ein Beweis, der von der rechnenden Maschine abhaengt, ist ein Muenzwurf. Nachgewiesen ist die Harmlosigkeit der Korrektur, nicht behauptet: das Python-Paket ergibt `6c47cd21...` unter beiden Sortierschluesseln auf beiden Plattformen, also bleibt die Vergleichbarkeit gegen `278fab52` der Nachmessung unangetastet, und der einzige Wert, der sich bewegt, war auf mehr als einer Maschine nie gueltig.

**Warum die Instanzzaehlung der gefaehrlichere der beiden Fehler war.** Auf dieser Box laeuft die All-in-One-Instanz als `ghcr.io/nextcloud-releases/aio-nextcloud:latest`; das Muster nannte die Docker-Hub-Form `nextcloud/aio-nextcloud`. Gezaehlt wurden 0 bei genau einer laufenden Nextcloud, und beide Skripte haben verweigert. Das war sicher, und es war trotzdem falsch. Die Gegenprobe zeigt, warum: **mit** der zweiten, handgebauten Nextcloud vom 07.09. auf demselben Docker-Dienst haette das alte Muster genau 1 gezaehlt und `--rm-data` durchgelassen, in genau der Lage, fuer die die Zaehlung existiert. Der Schutz haette im Ernstfall versagt und im Normalfall gebremst. Sechs Zusicherungen fahren das Muster jetzt gegen die neun echten Abbilder dieser Box, gegen die zweite Instanz und gegen die Begleitcontainer.

**Warum die Grundlast einen Umweg gebraucht hat.** Der Ablaufplan setzt Schritt 4 (`findling:index --restart -n`, Warteschlange fuellen) vor Schritt 5 (Grundlast im Leerlauf, "Modell nie geladen, noch keine Suche"). Auf dieser Maschine widerspricht sich das: Schritt 3 schaltet die PHP-App ein, also bedient der Poller die Warteschlange sofort, laedt fuer die Einbettungen das Modell und macht den Leerlauf zu einer Behauptung. Der Vorlaeufer hat die Grundlast **vor** dem Restart gemessen, wo die Warteschlange leer war. Statt die Zahl mit einem Vorbehalt zu berichten, ist der Zustand hergestellt worden, den die Zahl braucht: PHP-App aus, Container neu gestartet (nach DI-05-36 indexiert er dann nicht), Grundlast gemessen, erste Suche gemessen, und erst unmittelbar vor dem Anstoss die App wieder ein. Der Beleg steht in der Rohdatei als `pass-finished lines since this start: 0`, und der Preis, 1.653 schon indexierte Dateien beim Anstoss, steht im Ablaufplan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `aws_box.sh status` zaehlte jede Parkstunde als Laufstunde**

- **Found during:** Task 2, beim ersten folgenlosen Aufruf vor der Anfahrt
- **Issue:** `cmd_status` rechnet die Spanne von `LaunchTime` bis jetzt als Laufzeit, ohne den Zustand zu pruefen. Eine angehaltene Instanz antwortet weiter mit der `LaunchTime` ihres letzten Starts, also meldete der Aufruf `running 52.3 hours` und `spent 5.80 USD` fuer eine Box, die 1,95 Stunden gelaufen und seit dem 07.09. 06:56:42Z geparkt war. Genau die Falle, um die `cmd_stop` herum gebaut ist (dort liegt die Lesung bewusst vor dem Anhalten, mit einem Test darauf). An dieser Zahl haengt der Kostendeckel von 30 Stunden aus dem Owner-Checkpoint, und Task 4 dieses Plans laesst sie ausdruecklich gegen den Deckel pruefen.
- **Fix:** Die Rechnung ist an `State.Name` geknuepft. Bei laufender Instanz unveraendert; im geparkten Fall sagt sie, dass die Spanne keine Laufzeit ist, nennt die Tagesrate der Datentraeger und rechnet die Parktage ausdruecklich nicht zusammen.
- **Files modified:** `scripts/ops/aws_box.sh`, `backend/tests/test_ops_scripts.py`
- **Verification:** Nach der Korrektur meldet die laufende Box `running 0.0 hours since 2026-09-09T09:19:50` und `spent 0.00 USD`; `sh -n` ohne Befund; Gate 47 passed
- **Committed in:** `5a1356f`

**2. [Rule 1 - Bug] Die Instanzzaehlung vor `--rm-data` erkannte die Nextcloud dieser Box nicht, und haette die zweite durchgelassen**

- **Found during:** Task 2, Schritt 1, der mit Rueckgabewert 5 abbrach
- **Issue:** `SERVER_IMAGES` nannte `nextcloud/aio-nextcloud`, diese Box fahrt `ghcr.io/nextcloud-releases/aio-nextcloud:latest`. Gezaehlt wurden 0 bei genau einer laufenden Instanz, also Abbruch 5 in `90-bestand.sh` und Verweigerung von `--rm-data` in `92-wechsel.sh`. Die gefaehrliche Richtung ist die andere: mit der zweiten, handgebauten Nextcloud vom 07.09. (`nextcloud:34.0.3-apache`) zaehlte das alte Muster genau **1** und haette den zerstoerenden Befehl durchgelassen.
- **Fix:** Das Muster haengt am Repositoriumsnamen (`(^|/)aio-nextcloud:|(^|/)nextcloud:`) statt an einem Registry-Pfad; die handgebaute Form bleibt daneben. Sechs Zusicherungen fahren es gegen die neun echten Abbilder der Box, gegen die zweite Instanz (muss 2 ergeben) und gegen die fuenf Begleitcontainer, die das Wort nextcloud tragen und keine Server sind.
- **Files modified:** `90-bestand.sh`, `92-wechsel.sh`, `backend/tests/test_measurement_scripts.py`
- **Verification:** Schritt 1 danach `nextcloud-instanzen 1`, `nextcloud-einzahl ja`, Rueckgabewert 0; Gate 174 passed; beide Skripte byteweise gegen den Commit auf die Box kopiert
- **Committed in:** `6532015`

**3. [Rule 1 - Bug] Der Baumhash haing an der Maschine, die ihn ausrechnet, und hatte CI seit Welle 1 rot**

- **Found during:** Task 2, als die Pruefung des Plans am php-Erwartungswert scheiterte
- **Issue:** `40b-baumhash.py` sortierte Path-Objekte statt der posix-Pfade, die es hasht. Ergebnis: php ergab `26b55908...` auf Windows und `4a4c6f62...` auf der Box, bei 58 Dateien, die Datei fuer Datei byteweise identisch sind (nachgewiesen mit einem Vergleich aller 58 Inhaltshashes und Groessen). CI auf `ubuntu-24.04` war genau daran seit Welle 1 rot, Laeufe `34324820951` und `34333595918`, mit `AssertionError: assert '4a4c6f62...' == '26b55908...'`; die Wellen 1 bis 4 haben nur unter Windows geprueft und es deshalb nicht gesehen.
- **Fix:** Sortierschluessel ist der relative posix-Pfad, also genau das, was der Docstring des Rezepts immer vorschrieb. `PHP_TREE_HASH` auf `4a4c6f62...` korrigiert, der alte Wert steht mit seinem Grund daneben. Eine neue Zusicherung stellt die zwei Namen nach, die es ausgeloest haben (`Unit/` und `bootstrap`), und rechnet die Erwartung mit posix-Ordnung nach, wird also auf jeder Plattform rot, wenn der Schluessel zurueckgeht.
- **Belegte Harmlosigkeit:** das Python-Paket ergibt `6c47cd21...` unter **beiden** Sortierschluesseln auf **beiden** Plattformen. Keine berichtete Vergleichszahl wird retiriert, die Warnung im Docstring greift hier nicht.
- **Files modified:** `40b-baumhash.py`, `backend/tests/test_measurement_scripts.py`
- **Verification:** ganze Suite 1968 passed / 15 skipped gegen die Grundlinie 1960 / 15; `ruff`, `ruff format`, `pyright` ohne Befund; der Beweisschritt auf der Box erneut gefahren, `baumhash-gleich ja` mit `4a4c6f62...` fuer php
- **Committed in:** `7f121f3`

**4. [Rule 3 - Blocking] Nextcloud verlangte ein App-Upgrade, und deshalb gab es den Namensraum `app_api:app` nicht**

- **Found during:** Task 2, Schritt 3, der mit Rueckgabewert 9 abbrach
- **Issue:** Nach dem Einspielen der PHP-Haelfte fuehrte die Datenbank `findling: 1.0.0`, der Code trug 1.0.3. Nextcloud lief damit im eingeschraenkten Modus (`Nextcloud or one of the apps require upgrade`) und blendete `app_api:app:register` aus; die Registrierung fiel aus, der Container wurde nicht neu erzeugt, und die harte Grenze konnte nicht gesetzt werden, was den Abbruch 9 erklaert. Der `unregister --rm-data` davor war **erfolgreich** und hat nur diese Instanz getroffen (Zaehlung 1, Volumen danach leer), der Nullstand war also da.
- **Fix:** `occ upgrade`, der Befehl, den die Meldung selbst nennt. `Updated <findling> to 1.0.3`, `Update successful`, Wartungsmodus danach aus, `app_api:app:list` antwortet wieder. Danach Schritt 3 vollstaendig erneut, damit die Rohdatei einen zusammenhaengenden Schritt traegt.
- **Files modified:** keine (ein Zustand auf der Box, kein Code)
- **Verification:** Schritt 3 danach Rueckgabewert 0, `register-ende` gesetzt, `memory.max=2147483648`, `grenze-gesetzt ja`, ExApp `findling_backend 1.0.3 [enabled]`
- **Committed in:** kein Codecommit; protokolliert in `92-wechsel.txt` und hier

**5. [Rule 2 - Missing critical functionality] Die Grundlast wurde auf einem Container gemessen, der beweisbar nichts tat**

- **Found during:** Task 2, zwischen Schritt 4 und Schritt 5
- **Issue:** Schritt 4 stoesst `findling:index --restart -n` an und fuellt die Warteschlange; weil Schritt 3 die PHP-App einschaltet, begann der Poller sofort zu arbeiten (`claimed=10 indexed=2 embedded=8` je Durchgang) und lud fuer die Einbettungen das Modell. Schritt 5 soll aber die "Grundlast im Leerlauf, Modell nie geladen, noch keine Suche" messen, und `94-grundlast.sh` liest die cgroup, wie sie ist. Gemessen worden waere eine laufende Indexierung mit dem Namen einer Leerlaufmessung: die MESS-01-Kernzahl, und genau die Fehlerart, deren Reparatur der Gegenstand dieser Phase ist.
- **Fix:** Vor Schritt 5 die PHP-App abgeschaltet (der Poller bekommt keine Antwort mehr und geht ins Backoff) und den Container neu gestartet, damit das Modell entladen ist und dieser Start noch keine Suche gesehen hat. Nach Schritt 6 die App wieder abgeschaltet, damit der Anstoss in Task 3 ein echter Anstoss ist, und erst unmittelbar davor wieder ein.
- **Belege, die mitlaufen:** `pass-finished lines since this start: 0` in `94-grundlast.txt`; die Wortliste dieses Starts traegt dieselben 276.496 Eintraege und baut denselben Automaten wie die Vorlaeufer, also ist die Zahl vergleichbar und nicht durch ein leeres Volumen geschoent; `95-spitze-vorher.txt` zeigt 0 Poller-Durchgaenge waehrend der einzelnen Suche.
- **Files modified:** `00-ablauf.md` (der neue Abschnitt 0 nennt Reihenfolge, Grund und Preis)
- **Verification:** Schritt 5 Rueckgabewert 0, `grundlast-erwartung getroffen`, Teil D vollstaendig; Schritt 6 Rueckgabewert 0 mit genau einer Suche und ohne stoerenden Indexdurchgang
- **Committed in:** `e3ec58b`, `0bbfd9f`

### Kleinere Abweichungen, ohne eigene Regel

- **Der A-Record ist nicht gesetzt, sondern gemeldet.** Der Owner zieht ihn selbst; die neue Adresse ist **3.69.147.2**. Bis dahin greift Rueckfall 1, und Fallstrick 7 hat dabei genau wie vorhergesagt zugeschlagen: der Pin stand auf `172.18.0.4`, der Apache dieser Maschine sitzt auf `172.18.0.9`. Der Pin ist neu aus `docker inspect` gebildet, die gefundene Adresse steht im Protokoll, und die Gegenprobe ueber den Namen antwortet 200 von `172.18.0.9`. Gewaehlt wurde der Pin und nicht `curl --resolve`, weil alle sieben Skripte nur `BASE` kennen und mitten im Lauf nicht angefasst werden sollten; der Preis (ein Maschinenneustart macht den Pin erneut stumpf) steht in `89-anfahrt.txt`.
- **Die Ausgabe von `status` und `prices` steht in einer eigenen Rohdatei `89-anfahrt.txt`**, weil das Akzeptanzkriterium sie im Protokoll verlangt und die Anfahrt von diesem Windows-Rechner laeuft, also von keinem Box-Skript geschrieben wird. Die Datei ist als von Hand geschrieben gekennzeichnet.
- **Schritt 1 und Schritt 3 sind je zweimal gefahren**, das erste Mal mit Abbruch 5 beziehungsweise 9. Beide Male war der Abbruch richtig und die Ursache eine andere als vermutet; die Rohdateien tragen den vollstaendigen zweiten Lauf, und die Gruende stehen unter Deviations 2 und 4.
- **Der Beweisschritt ist nach der Korrektur des Rezepts erneut gefahren.** `40b-baumhash.txt` traegt deshalb den plattformunabhaengigen Stand, `92-wechsel.txt` den, den der Schritt zum Zeitpunkt seines Laufs gesehen hat. Die beiden php-Zeilen unterscheiden sich, und der Grund steht hier und im Commit; ueberschrieben wurde nichts.
- **Der Prueflauf des Plans fuer Task 2 erwartet den php-Baumhash `26b55908...`.** Diese Zusicherung kann auf der Box nicht halten und soll es nicht: sie nennt das Windows-Artefakt. Geprueft wurde gegen `4a4c6f62...`, und die Pruefung ist zusaetzlich um Bytezahl, Instanzzaehlung, Urteilszeile und Kaltstartzeile erweitert worden.
- **Der Prueflauf des Plans fuer Task 3 nennt die Dateinamen `00-start.txt`, `statusseite.jsonl` und `vergleichsmessung.csv`.** Gebaut wurden sie in Welle 4 mit dem 96er-Praefix (`96-volllauf-start.txt`, `96-statusseite.jsonl`, `96-volllauf.csv`), und `00-ablauf.md` fuehrt sie so. Geprueft wurde gegen die echten Namen, inhaltlich strenger als der Plan verlangt (die drei Werte der Trockenprobe woertlich, der Anstosszeitpunkt, der Rundendeckel).
- **Auf der Box liegt ein Checkout unter `/home/ubuntu/work/repo0918`**, gestellt auf `5d325ed`, also genau den Stand der Wellen 1 bis 4, mit leerem `git status`. Die Skripte leiten `REPO` aus ihrer eigenen Lage ab und brauchen ihn; alle Helfer lagen an den Vorgabepfaden. Die drei korrigierten Dateien sind byteweise gegen den Commit auf die Box kopiert (sha256 beidseitig verglichen).
- **Vier leere `.err`-Dateien sind nicht committet.** Sie belegen nur, dass keine Standardfehlerausgabe anfiel; die zugehoerigen JSON-Antworten liegen daneben.

### Aus Task 4, nach dem Lauf festgestellt und nicht mehr reparierbar

Beide sind Befunde des Laufs und keine Eingriffe: der Lauf war zu Ende, bevor sie sichtbar wurden, und der Container darf bis 10-06 nicht angefasst werden.

- **Die Suchlastprobe "am Uebergang der Spuren" ist in Runde 1 gefallen.** `SCHWELLE=200` in `96b-waechter.sh`, aber beim Anstoss standen schon 264 Vektoren, also war die Schwelle vor der ersten Lesung ueberschritten. Gemessen wurde ein p95 bei 1.679 Dokumenten (409,9 ms) statt am Uebergang. Dieselbe Wurzel wie der Untergrenzen-Vorbehalt. Im Bericht eine benannte Fehlstelle; das Gegenstueck, das traegt, ist die Probe am Ende. Fuer einen naechsten Lauf muesste die Schwelle relativ zum Startpunkt stehen (`embedded` groesser `startpunkt-embedded` plus 200) und nicht absolut.
- **Die Fertigmeldung ist doppelt gesendet worden**, einmal aus dem Waechter (`modus=senden`, 13:05:11Z) und einmal aus der wartenden Haelfte, die `00-FERTIG` selbst gesehen hat (13:09:45Z). Beide mit `http=200`. Harmlos und sogar redundant nuetzlich, aber ein Riegel in `96e-ntfy-watch.sh` waere billig.
- **Die Erwartung "`max` auf null" aus dem Ablaufplan ist nicht eingetreten.** Gemessen 21.939 gegen 2.796 in 06-11. Die Erwartung bleibt so stehen, wie sie formuliert war, und der gemessene Wert steht daneben. Es wird nichts nachtraeglich umgeschrieben.

---

**Total deviations:** 5 auto-fixed (3x Rule 1 Bug, 1x Rule 3 Blocking, 1x Rule 2 fehlende kritische Funktionalitaet) plus sieben kleinere Abweichungen aus den Tasks 1 bis 3 und drei Befunde aus Task 4
**Impact on plan:** Kein Scope Creep, kein Paket installiert, `backend/uv.lock` unveraendert, keine Zeile unter `php/` und keine Zeile in `backend/src/`. Drei der fuenf drehen sich um denselben Punkt wie die ganze Phase: eine Zahl, die falsch ist und wie eine Messung aussieht. Eine davon hatte CI seit Welle 1 rot, und zwei betrafen Schutzmechanismen, die im Ernstfall versagt haetten. Aus Task 4 kam keine Codeaenderung, weil jede Codeaenderung an den Messskripten nach dem Lauf nur noch ein naechstes Mal betraefe und die Befunde deshalb dort stehen, wo sie gelesen werden.

## Issues Encountered

**Der Beweis, der die Phase tragen soll, war selbst maschinenabhaengig.** Das ist der Befund, der am meisten Zeit gekostet hat und der am wenigsten erwartet war. Die Phase existiert, weil zwei Berichte eine Gleichheit behauptet und ihren Beweis leer gelassen haben. Welle 1 hat den Beweis gebaut, und der Beweis rechnete auf zwei Maschinen zwei Ergebnisse aus, ohne es zu sagen. Gefunden wurde er nicht durch Nachdenken, sondern weil die Pruefung des Plans an einem Erwartungswert scheiterte und die naechste Frage nicht "welcher Wert ist richtig" war, sondern "sind die Dateien ueberhaupt verschieden". Sie waren es nicht: 58 von 58 identisch, nur anders sortiert.

**Zwei Schutzmechanismen waren stumm falsch, und beide in der billigen Richtung.** Die Instanzzaehlung verweigerte, wo sie zaehlen sollte, und haette gezaehlt, wo sie verweigern sollte. Die Kostenrechnung meldete das Sechsundzwanzigfache der wirklichen Laufzeit, in einem Unterbefehl ohne Nebenwirkung, dessen Zahl der Owner-Deckel prueft. Beide haetten in einem Lauf ohne Gegenlesen niemandem auffallen muessen.

**Die Reihenfolge des Ablaufplans und ihre eigene Zusage passten an einer Stelle nicht zusammen.** Schritt 4 startet die Arbeit, Schritt 5 will den Leerlauf messen. Auf dem Papier stand beides nebeneinander, auf der Maschine schliesst das eine das andere aus. Aufgefallen ist es an einer Log-Zeile mit `embedded=8`, also daran, dass das Modell schon geladen war. Der Vorlaeufer hat die Grundlast vor dem Restart gemessen; diese Welle hat den Zustand wiederhergestellt statt die Zahl mit einem Vorbehalt zu berichten, und den Preis dafuer ausgewiesen.

**Nextcloud lief nach dem Einspielen der PHP-Haelfte im eingeschraenkten Modus.** Die Datenbank fuehrte 1.0.0, der Code 1.0.3, und ein `occ` im Upgrade-Modus hat den Namensraum `app_api:app` gar nicht. Die Fehlermeldung des Skripts nannte die harte Grenze, die Ursache lag drei Abschnitte darueber. Das ist eine Zeile, die in `00-ablauf.md` fuer die naechste Anfahrt fehlt.

**Der Lauf hat 40,9 Prozent laenger gebraucht als sein Vorlaeufer, und der naheliegende Verdaechtige ist es nicht gewesen.** Die Vermutung beim ersten Blick auf `memory.peak` gleich `memory.max` und `max` gleich 21.939 war eine Maschine, die sich unter Speicherdruck langsam zusetzt. Der Durchsatz sagt etwas anderes: 34,1 / 33,1 / 32,7 / 32,5 / 34,6 / 32,7 Dokumente je Minute ueber sechs Bloecke zu je 200 Minuten, quer durch die Nacht, waehrend der Container die ganze Zeit an der Grenze stand. Das ist keine Verschlechterung, das ist ein Plateau. Was ueber den ganzen Lauf gleichmaessig fehlt, ist eher ein Zulauf als eine Bremse, und `vorrat=0` in 19,1 Prozent der Lesungen zeigt in diese Richtung. Bewiesen ist es damit nicht; die Aussage dieses Plans ist die Zahl und der Ausschluss, nicht die Ursache.

**Der Nebenbefund 52.111 hat sich ohne einen einzigen Zugriff auf den Container aufklaeren lassen.** Der erste Reflex war die Verdiktverteilung, also genau die Stelle, an der der Plan 10-06 eine Abweichung erwartet. Sie war es nicht: `skipped` steht in beiden Laeufen auf exakt 37. Die Antwort lag im Dateisystem, in zwei Verzeichnissen mit Aenderungsdatum 07.09., und die Summe stimmt auf das Dokument genau. Die Lehre ist die billigere Reihenfolge: bei einer Mengenabweichung erst zaehlen, was da ist, dann fragen, was damit passiert ist.

## User Setup Required

**Ein Handgriff aus Task 1 ist erledigt, ein Entscheid aus Task 4 ist offen.**

> **Erledigt:** der A-Record `loadtest.infranode.dev` zeigt auf `3.69.147.2`. Der Owner hat ihn am 09.09. gezogen; der Lauf hat 27 Stunden lang ueber diesen Namen gearbeitet, und die Meldekette hat viermal mit `http=200` geantwortet, wo am 05.09. ein 403 stand.

> **OFFEN und eilig, Owner-Entscheid vor Plan 10-06:**
> **Die Box hat noch 2,1 Stunden unter dem 30-Stunden-Deckel** (27,9 h gelaufen, 3,23 USD von 3,50 USD, Deckel erreicht am **2026-09-10T15:19:50Z**). Plan 10-06 braucht darunter: OOM-Beweis (liegt schon vor, wird nur geprueft), Bestand und Verdikte, die Nebenlaeufigkeitsreihe mit 410 Anfragen, den bewussten Neustart mit Kaltstart auf vollem Bestand, die Seitenroute, die Rundenzaehlung und die zehn Sprachfaelle (allein rund 30 Minuten laut Owner-Freigabe). Das ist knapp und moeglicherweise zu knapp.
> **Zu entscheiden:** entweder 10-06 sofort und straff fahren und notfalls die Sprachfaelle als Letztes opfern, oder den Deckel auf 33 bis 34 Stunden und 4,00 USD anheben (Mehrkosten rund 0,47 USD). Wird nichts entschieden, gilt der Deckel: was bis 15:19:50Z erhoben ist, wird gesichert, der Rest wird als offen benannt, und die Box wird angehalten.

## Next Phase Readiness

**Der Lauf ist durch, Task 4 ist beantwortet, und dieser Plan ist abgeschlossen.** Stand beim Schreiben dieser Zeile (2026-09-10, rund 13:40Z):

- Volllauf fertig, `00-FERTIG` liegt und ist committet, Waechter in Runde 325 von 340 aus eigenem Urteil beendet
- 52.111 indexiert und eingebettet, 37 uebersprungen, 0 fehlgeschlagen; die 150 gegen 06-11 sind aufgeklaert
- **Container unangetastet:** `RestartCount=0`, `Status=running`, `StartedAt=2026-09-09T09:40:51Z`, `OOMKilled=false`
- `memory.peak` 2.147,5 MB gleich der harten Grenze, `max` 21.939, `oom`, `oom_kill` und `oom_group_kill` je 0
- alle vier abgesetzten Beobachter sind von selbst zu Ende gegangen, `pgrep` findet keinen mehr
- Box 27,9 h gelaufen, 3,23 USD von 3,50 USD Deckel, **Rest 2,1 h**
- alle Rohdaten des Laufs sind von der Box geholt und committet (`5d276dd`)

Fuer Plan 10-06 liegt bereit: der OOM-Beweis steht in `96-oom-beweis.txt` und ist **vor jedem Eingriff** erhoben, also findet `95-spitze.sh nachher` die Datei und bricht nicht mit 12 ab, und der bewusste Neustart in Task 2 ist gedeckt. `jq` liegt auf der Box, also verweigern `98-sprachfaelle.sh` und `99b-runden.sh` nicht mit 18. Beide Passwortdateien liegen mit Modus 600 an den Stellen, die die `PWFILE`-Vorgaben erwarten. Die Owner-Antworten aus Task 1 legen den Umfang fest: Sprachfaelle auf der Box **ja** und im Bericht als Erstmessung auszuweisen, DI-07-02 und DI-07-03 **beide**.

Drei Dinge, die 10-06 aus diesem Task mitnimmt und nicht neu suchen muss:

1. **Die Abweichung 52.111 gegen 51.961 ist keine Panne und keine Verdiktverschiebung.** Sie ist erklaert (`ocrdrei` 120 plus `neustart` 30, angelegt am 07.09.), und `skipped` steht in beiden Laeufen auf exakt 37. Task 1 Punkt 5 kann darauf aufsetzen statt es zu erarbeiten. Was dort noch zu klaeren bleibt, ist der Versatz von plus 34 zwischen Verdikten und Dateizaehlung, der in beiden Laeufen identisch ist.
2. **Die Phasengrenze "Uebergang der Spuren" gibt es in diesem Lauf nicht**, weil beide Spuren gekoppelt liefen. `rss_digest.py` braucht in Task 1 Punkt 3 eine andere Grenzziehung als in 06-11, und die Suchlastprobe, die "am Uebergang" heisst, ist in Runde 1 gefallen.
3. **Der Zeitdruck ist real.** Der Deckel bindet in rund zwei Stunden, und Task 1 von 10-06 ist der Teil, dessen Zahlen fluechtig sind: sie leben in der cgroup dieses Containers und sind nach dem Neustart in Task 2 weg. Die Reihenfolge des Plans ist damit nicht nur richtig, sondern dringend.

**Requirements:** MESS-01, MESS-02 und MESS-03 bleiben `Pending`. MESS-01 hat seine Kernzahl und jetzt auch die Laufzeit, MESS-02 hat eine duenne p95-Zeile bei vollem Bestand, aber die belastbare Reihe und der Bericht fehlen; abhaken darf sie der Plan, der die Zahlen zusammentraegt. `REQUIREMENTS.md` ist in keinem Commit dieses Plans.

## Known Stubs

Keine. Jede Zahl dieses Plans ist auf der Box gemessen, jede Rohdatei ist nicht leer, und die vier Urteilszeilen, an denen der Lauf haette scheitern sollen (`korpus-gleich`, `baumhash-gleich`, `grenze-gesetzt`, `ende-erkannt`), tragen alle vier ein `ja`.

Was jetzt vorliegt und beim Schreiben der ersten Fassung dieser Zeilen noch fehlte: die Laufzeit, `memory.events` ueber den ganzen Lauf, `memory.peak` des ganzen Laufs, der OOM-Beweis, Bestand und Verdikte, und eine erste p95-Zeile bei vollem Bestand.

Was weiter fehlt, fehlt nicht als Stub, sondern als naechster Plan: die Spitzen getrennt nach Phase, die Nebenlaeufigkeitsreihe mit 410 Anfragen, der Kaltstart auf vollem Bestand nach dem bewussten Neustart, die zehn Sprachfaelle, die Seitenroute, die Rundenzaehlung und der Endungsvergleich. Alle sieben stehen in Plan 10-06.

Zwei benannte Fehlstellen, die kein Stub und keine Auslassung sind, sondern gemessene Luecken: der p95 "am Uebergang der Spuren" ist bei 1.679 statt bei zehntausenden Dokumenten gefallen (Grund oben), und der Versatz von plus 34 zwischen Verdikten und Dateizaehlung ist unerklaert, in beiden Laeufen identisch und damit fuer den Vergleich folgenlos.

## Threat Flags

Keine neue Angriffsflaeche. Die Eintraege mit Disposition `mitigate`, und was dieser Lauf dazu belegt:

| Threat ID | Umsetzung, gemessen |
|-----------|---------------------|
| T-10-28 | `91-korpus.sh` lief VOR dem Indexaufbau, `korpus-gleich ja` gegen `bcbef9b2...` und 20.208.046.426 Byte |
| T-10-29 | `40b-baumhash.txt` traegt drei `baumhash:`-Zeilen und `baumhash-gleich ja`. Zusaetzlich ist der Beweis jetzt plattformunabhaengig, was er vorher nicht war |
| T-10-30 | `memory.max=2147483648` aus der cgroup zurueckgelesen, nach der Registrierung neu gesetzt, in `92-wechsel.txt` und erneut in `94-grundlast.txt` |
| T-10-31 | `nextcloud-instanzen 1` in `90-bestand.txt` und in `92-wechsel.txt`, letzteres in der folgenlosen Phase A vor `--rm-data`. Die Zaehlung selbst ist korrigiert, weil sie die zweite Instanz durchgelassen haette |
| T-10-32 | Die Trockenprobe des Lesers steht mit ihrer Ausgabe im Protokoll und traf eine echte Aufnahme: `2040 1653 264`, aus `backend`. **Nach dem Lauf belegt:** 325 Lesungen ohne ein einziges `unklar`, `ende-erkannt ja` in Runde 325 von 340. Der Waechter war nicht blind, und der Lauf ist nicht am Rundendeckel geendet |
| T-10-33 | `aws_box.sh start` hat die SSH-Regel gezogen, revoke vor authorize; Port 22 zeigt auf `77.3.136.241/32` und auf nichts sonst |
| T-10-34 | Kein Passwort und kein Token in einer Rohdatei, geprueft mit dem Inhalt beider Passwortdateien gegen alle committeten Rohdaten: 0 Treffer. Passwoerter reisten ueber `--password-env` und `sudo cat`, nie in einem Argument |
| T-10-35 | Der `/etc/hosts`-Pin ist neu aus `docker inspect` gebildet, die gefundene Adresse (`172.18.0.9`) steht im Protokoll, und der A-Record ist dem Owner mit der neuen Adresse gemeldet |
| T-10-36 | Die Rohdaten der Grundlast und der ersten Suche sind in `e3ec58b` committet, **bevor** der Volllauf angestossen wurde |
| T-10-37 | Beide Wartefristen liefen 360 s gegen die langsamste Uhr; die Gegenprobe kam nach 361 s. Das Urteil des Skripts steht unveraendert, der Nachtrag darunter |
| T-10-SC | Kein Paket installiert, kein Abbild auf der Box gebaut. Das Abbild kam per `docker pull` aus ghcr, `backend/uv.lock` unveraendert |

**Ein Befund, der in den Bericht gehoert und keine Bedrohung ist:** `digest-gleich nein`. Gemessen `sha256:78ab61d8...`, in Plan 10-02 notiert `eed6a5fc...` (Manifestindex) beziehungsweise `ae58d930...` (arm64-Haelfte). Das Skript behandelt das als benannten Befund und nicht als Abbruch, und es hat recht: `:dev` ist ein wandernder Zeiger, der Pfadfilter von `docker.yml` reicht in `backend/**`, und die Wellen 1 bis 4 haben dort Testdateien committet. Der Vergleich, der traegt, ist der Baumhash, und der stimmt exakt.

## Self-Check: PASSED

| Geprueft | Ergebnis |
|----------|----------|
| Alle 14 Rohdateien aus `key-files.created` liegen auf der Platte | 14x `FOUND`, keine leer |
| Alle sieben Commits in `git log` | `5a1356f`, `6532015`, `7f121f3`, `e3ec58b`, `2a37a60`, `0bbfd9f` und dieser Metadaten-Commit |
| Loeschungen in den Commits | keine (`--diff-filter=D` leer) |
| Datei unter `php/` oder `backend/src/` im Diff | keine |
| Prueflauf Task 2 (sieben Rohdateien, Baumhash, Korpus, harte Grenze, Grundlast, Kaltstart) | `ok` |
| Prueflauf Task 3 (vier Rohdateien, Trockenprobe woertlich, Anstoss, Rundendeckel, HTTP-Code, kein Namenstraeger) | `ok` |
| `git status --porcelain backend/appinfo/info.xml` | leer, und `92-info-box.xml` liegt in den Rohdaten |
| Rohdaten byteidentisch mit der Box | sieben `.txt` verglichen, CR=0, Byte- und LF-Zahl gleich |
| Passwort in einer Rohdatei | 0 Treffer gegen den Inhalt beider Passwortdateien |
| `pytest -q` (ganze Suite) | 1968 passed / 15 skipped (Grundlinie 1960 / 15, plus acht neue Zusicherungen) |
| `ruff check`, `ruff format --check`, `pyright` | ohne Befund |
| `sh -n` ueber die drei geaenderten Shellskripte | ohne Befund |
| Wagenruecklauf, Em-Dash oder En-Dash in den neuen Dateien | keiner |
| Skripte auf der Box byteidentisch mit dem Commit | `90-bestand.sh`, `92-wechsel.sh`, `40b-baumhash.py` je sha256 beidseitig gleich |
| `.planning/REQUIREMENTS.md` unveraendert | nicht im Diff |
| `CLAUDE.md` unveraendert | nicht im Diff |
| Vier abgesetzte Prozesse laufen (Stand 09.09.) | Sampler, Statusbeobachter, Waechter, Meldekette, mit `pgrep` belegt |

### Nachtrag zum Self-Check, nach Task 4 (2026-09-10)

| Geprueft | Ergebnis |
|----------|----------|
| Die fuenf neuen Rohdateien liegen und sind nicht leer | 5x `FOUND` |
| Die fuenf nachgezogenen Rohdateien tragen den vollstaendigen Lauf | 19.485 CSV-Zeilen, 812 Statusaufnahmen, 493 Waechterzeilen, 8 Meldekettenzeilen |
| Alle zehn Rohdateien byteidentisch mit der Box | 10x `sha256` beidseitig gleich |
| Wagenruecklauf in den zehn Rohdateien | `CR=0` in allen zehn |
| Passwort in einer der zehn Rohdateien | **0 Treffer** gegen den Inhalt aller drei Passwortdateien (`admin`, `arm64-admin`, `lasttest`), auf der Box geprueft, damit kein Passwort die Box verlaesst |
| Namenstraeger in `96-statusseite.jsonl` | 0 Treffer auf `.pdf`, `.docx`, `/files/` und den Nutzernamen |
| Prueflauf Task 4 (elf Rohdateien, `00-FERTIG` woertlich, sieben OOM-Zaehler, 325 Lesungen ohne `unklar`, kein Rundendeckel, vier `http=200`, Verdikte, beide p95, Laufzeitarithmetik, fuenfzehn Zahlen der SUMMARY) | `ok` |
| Rundendeckel erreicht | nein, `runde=326` kommt im Protokoll nicht vor |
| Container angefasst | nein: `RestartCount=0`, `StartedAt=2026-09-09T09:40:51Z` unveraendert in beiden OOM-Lesungen |
| `occ` oder `docker exec` in diesem Task | keiner; nur `cat`, `tail`, `ls`, `find`, `awk`, `sha256sum`, `grep` und `aws_box.sh status` |
| Commits von Task 4 in `git log` | `5d276dd` und dieser Metadaten-Commit |
| Loeschungen in `5d276dd` | keine (`--diff-filter=D` leer) |
| Datei unter `php/` oder `backend/src/` im Diff von Task 4 | keine; Task 4 hat keine Zeile Code geaendert |
| Wagenruecklauf, Em-Dash und En-Dash in der SUMMARY | keiner, keiner, keiner |
| Das vom Vokabular-Gate verbotene Wort in der SUMMARY | 0 Treffer |

## TDD Gate Compliance

Nicht anwendbar als Plan-Gate: der Plan traegt `type: execute` und keine Aufgabe ist mit `tdd="true"` ausgezeichnet. Die drei Korrekturen sind trotzdem mit ihrer Zusicherung committet, und zwei von ihnen sind gegen einen gestellten Fall gefahren, der ohne Box rot wird: die Instanzzaehlung gegen die neun echten Abbilder plus die zweite Instanz, und der Sortierschluessel gegen die zwei Namen, die den Unterschied ausgeloest haben.

---
*Phase: 10-vergleichsmessung-auf-der-aws-box*
*Completed: 2026-09-10 (alle vier Tasks; Task 4 war ein blockierender Checkpoint ueber 27 Stunden Laufzeit und ist mit dem Resume-Signal beantwortet)*
