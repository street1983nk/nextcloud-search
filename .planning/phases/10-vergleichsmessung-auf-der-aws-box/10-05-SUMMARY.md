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
  - "MESS-01 bis MESS-03 bleiben Pending. Der Lauf laeuft noch, der Bericht existiert nicht, und abhaken darf sie der Plan, der die Zahlen zusammentraegt"

patterns-established:
  - "Eine Zahl, an der ein Kostendeckel haengt, wird gegen den Zustand geprueft, aus dem sie stammt"
  - "Ein plattformabhaengiger Vergleich in einem Beweisschritt ist ein Fehler, auch wenn er auf der Maschine des Entwicklers stimmt"
  - "Eine Leerlaufmessung fuehrt den Beleg mit, dass Leerlauf war"

requirements-completed: []
requirements-touched: [MESS-01, MESS-02]

# Metrics
duration: 55min
completed: 2026-09-09
---

# Phase 10 Plan 05: Die Anfahrt, die Zahlen vor dem Volllauf und der abgesetzte Anstoss Summary

**Die Grundlast im Leerlauf ist von 691,8 MB auf 103,2 MB gefallen, gemessen auf einem Container, der beweisbar nichts tat, und der 19-Stunden-Lauf laeuft seit 09:58:42Z abgesetzt mit einem Ende, das eine Datei ist.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-09-09T09:15:00Z
- **Completed (Tasks 1 bis 3):** 2026-09-09T10:10:00Z
- **Tasks:** 3 von 4 ausgefuehrt, Task 4 ist ein blockierender Checkpoint ueber die Laufzeit
- **Box-Minuten:** 51 bis zum Anstoss, danach laeuft die Box weiter (0,1158 USD je Stunde)
- **Kosten bis zum Anstoss:** 0,09 USD netto von 3,50 USD Deckel

## Accomplishments

- **Die MESS-01-Kernzahl ist gemessen und sie ist der Befund, auf den die Phase hinauslief:** Grundlast im Leerlauf **103,2 MB** (`anon` 108.199.936 Byte) gegen **691,8 MB** aus 06-11 und **693,4 MB** aus der Nachmessung. Das sind 588,6 MB weniger, und es ist besser als die gerechnete Erwartung von 118 bis 150 MB. Der Beleg, dass Leerlauf war, steht daneben: null Poller-Durchgaenge seit dem Containerstart, Modell nie geladen, keine Suche. Der Stoerfaktor ist ausgeschlossen, weil dieser Start dieselbe Wortliste liest und denselben Automaten baut wie die Vorlaeufer (276.496 Eintraege, im Protokoll).
- **Die erste Suche als Ereignis, und sie bestaetigt die Deutung:** `anon` 103,2 auf 518,2 MB, also **plus 415,0 MB** fuer die ankommenden Gewichte, gegen plus 422,3 MB des Vorlaeufers. Dieselben Gewichte, dieselbe Bewegung, nur die Grundlast darunter ist weg.
- **Der Beweisschritt, den beide Vorlaeuferberichte LEER gelassen haben, ist nicht leer:** `40b-baumhash.txt` traegt drei `baumhash:`-Zeilen und ein Urteil. Abbild 54 Dateien `6c47cd21...`, Arbeitsbaum dieselben 54 und derselbe Hash, `baumhash-gleich ja`. Kriterium 1 ist damit belegt statt behauptet.
- **Der Korpus ist als dieselben Bytes belegt, vor dem Indexaufbau:** `korpus-gleich ja`, 50.000 Dateien, 20.208.046.426 Byte, `bcbef9b2...`, die arm64-Zeile. Annahme A3 ist gemessen und nicht uebernommen, und der Vergleich lief gegen die richtige der beiden Pruefsummen.
- **Die harte Grenze steht bei 2 GiB, aus der cgroup zurueckgelesen** und nicht aus dem Docker-Klienten: `memory.max=2147483648`, `memory.swap.max=0`, nach der Registrierung neu gesetzt, weil ein Register sie wegwirft.
- **Der Volllauf laeuft abgesetzt und kann nachts allein zu Ende kommen.** Anstoss 09:58:42Z, Gegenprobe nach 361 s mit `arbeitsvorrat-da ja`, 47 gezaehlte Poller-Durchgaenge als DI-05-36-Beweis. Sampler mit 5 s und vier Aufnahmen VOR dem Anstoss, Statusbeobachter mit 120 s, Waechter mit Rundendeckel 340, Meldekette mit `http=200`.
- **Die Trockenprobe des Lesers steht mit ihrer Ausgabe im Protokoll und trifft eine echte Aufnahme:** `2040 1653 264`. Vorrat, `indexed` und `embedded` aus `backend`, nicht die Null der obersten Ebene. Fallstrick 8, der teuerste Fehler beider Vorlaeufer, ist damit auf dieser Maschine geschlossen und nicht nur im Gate.
- **Drei Werkzeuge sind korrigiert, alle drei mit einer Zusicherung daneben, und eines davon hatte CI seit Welle 1 rot.** Die Einzelheiten stehen unter Deviations, weil jede der drei eine Zahl betraf, die falsch war und richtig aussah.

## Task Commits

1. **Task 1: Owner-Checkpoint** , kein Commit. Die Freigabe ist in `89-anfahrt.txt` woertlich protokolliert.
2. **Task 2, Korrektur 1: die Laufzeitrechnung von `status`** , `5a1356f` (fix)
3. **Task 2, Korrektur 2: die Instanzzaehlung vor `--rm-data`** , `6532015` (fix)
4. **Task 2, Korrektur 3: der Sortierschluessel des Baumhashes** , `7f121f3` (fix)
5. **Task 2: die Rohdaten vor dem Volllauf, Bestand bis erste Suche** , `e3ec58b` (feat)
6. **Task 2: das Protokoll der Anfahrt** , `2a37a60` (docs)
7. **Task 3: der Volllauf laeuft abgesetzt** , `0bbfd9f` (feat)

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
| `memory.events`, alle sechs Zaehler | 0, durchgaengig bis zum Stand dieser Zeile | `max` 2.796 in 06-11, 0 in der Nachmessung | `90-bestand.txt`, Waechter |
| `memory.peak` beim Schreiben dieser Zeile | 1.715,5 MB, Lauf laeuft | 1.837,8 MB (06-11), 1.812,7 MB (Nachmessung) | cgroup |

**Was diese Tabelle noch nicht sagt:** Gesamtspitze, Laufzeit und der p95 ueber den vollen Bestand entstehen erst am Ende des Laufs. Sie gehoeren in Plan 10-06.

**Und ein Vorbehalt, der zur Laufzeit gehoert:** beim Anstoss lagen bereits 1.653 der 50.000 Dateien im Index. Die gemessene Laufzeit ist deshalb eine **Untergrenze**, das Skript sagt es selbst in `startpunkt-bewertung`, und `00-ablauf.md` traegt den Grund.

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

---

**Total deviations:** 5 auto-fixed (3x Rule 1 Bug, 1x Rule 3 Blocking, 1x Rule 2 fehlende kritische Funktionalitaet) plus sieben kleinere Abweichungen
**Impact on plan:** Kein Scope Creep, kein Paket installiert, `backend/uv.lock` unveraendert, keine Zeile unter `php/` und keine Zeile in `backend/src/`. Drei der fuenf drehen sich um denselben Punkt wie die ganze Phase: eine Zahl, die falsch ist und wie eine Messung aussieht. Eine davon hatte CI seit Welle 1 rot, und zwei betrafen Schutzmechanismen, die im Ernstfall versagt haetten.

## Issues Encountered

**Der Beweis, der die Phase tragen soll, war selbst maschinenabhaengig.** Das ist der Befund, der am meisten Zeit gekostet hat und der am wenigsten erwartet war. Die Phase existiert, weil zwei Berichte eine Gleichheit behauptet und ihren Beweis leer gelassen haben. Welle 1 hat den Beweis gebaut, und der Beweis rechnete auf zwei Maschinen zwei Ergebnisse aus, ohne es zu sagen. Gefunden wurde er nicht durch Nachdenken, sondern weil die Pruefung des Plans an einem Erwartungswert scheiterte und die naechste Frage nicht "welcher Wert ist richtig" war, sondern "sind die Dateien ueberhaupt verschieden". Sie waren es nicht: 58 von 58 identisch, nur anders sortiert.

**Zwei Schutzmechanismen waren stumm falsch, und beide in der billigen Richtung.** Die Instanzzaehlung verweigerte, wo sie zaehlen sollte, und haette gezaehlt, wo sie verweigern sollte. Die Kostenrechnung meldete das Sechsundzwanzigfache der wirklichen Laufzeit, in einem Unterbefehl ohne Nebenwirkung, dessen Zahl der Owner-Deckel prueft. Beide haetten in einem Lauf ohne Gegenlesen niemandem auffallen muessen.

**Die Reihenfolge des Ablaufplans und ihre eigene Zusage passten an einer Stelle nicht zusammen.** Schritt 4 startet die Arbeit, Schritt 5 will den Leerlauf messen. Auf dem Papier stand beides nebeneinander, auf der Maschine schliesst das eine das andere aus. Aufgefallen ist es an einer Log-Zeile mit `embedded=8`, also daran, dass das Modell schon geladen war. Der Vorlaeufer hat die Grundlast vor dem Restart gemessen; diese Welle hat den Zustand wiederhergestellt statt die Zahl mit einem Vorbehalt zu berichten, und den Preis dafuer ausgewiesen.

**Nextcloud lief nach dem Einspielen der PHP-Haelfte im eingeschraenkten Modus.** Die Datenbank fuehrte 1.0.0, der Code 1.0.3, und ein `occ` im Upgrade-Modus hat den Namensraum `app_api:app` gar nicht. Die Fehlermeldung des Skripts nannte die harte Grenze, die Ursache lag drei Abschnitte darueber. Das ist eine Zeile, die in `00-ablauf.md` fuer die naechste Anfahrt fehlt.

## User Setup Required

**Ein Handgriff, und er ist der einzige:**

> **Der A-Record `loadtest.infranode.dev` ist in der Cloudflare-Zone auf `3.69.147.2` zu ziehen.**
> Die Box laeuft seit 2026-09-09T09:20:06Z unter dieser Adresse. Bis der Eintrag steht, arbeitet die Box mit dem `/etc/hosts`-Pin auf `172.18.0.9`, also laeuft nichts auf den alten Eintrag `3.77.150.91`. Der Lauf braucht den Record nicht, um weiterzulaufen; er beseitigt nur den Fallstrick, dass ein Maschinenneustart den Pin stumpf macht.

## Next Phase Readiness

**Der Lauf laeuft. Task 4 dieses Plans ist ein blockierender Checkpoint und steht offen**, weil ein abgesetzter Lauf von rund 19 Stunden in einer Sitzung nicht abgewartet werden kann. Was auf der Box unangetastet bleiben muss: der Container, weil `memory.peak` und `memory.events` des ganzen Laufs sonst verloren sind.

Stand beim Schreiben dieser Zeile (10:10Z, rund 11 Minuten nach dem Anstoss):

- Waechter laeuft, Runde 1 protokolliert, Rundendeckel 340 a 300 s
- `vorrat=1768 indexed=1679 embedded=280`, beide Spuren bewegen sich
- `anon` 1.535,9 MB, `memory.peak` 1.715,5 MB gegen die Grenze von 2.147,5 MB
- alle sechs `memory.events`-Zaehler auf **0**
- 23 GB frei auf `/mnt/findling`
- Box 0,8 h gelaufen, 0,09 USD von 3,50 USD Deckel
- `00-FERTIG` existiert noch nicht, wie erwartet

Fuer Plan 10-06 liegt bereit: der OOM-Beweis schreibt `96-oom-beweis.txt` bei erkanntem Ende vor jedem Eingriff, also findet `95-spitze.sh nachher` die Datei und bricht nicht mit 12 ab. `jq` liegt auf der Box, also verweigern `98-sprachfaelle.sh` und `99b-runden.sh` nicht mit 18. Beide Passwortdateien liegen mit Modus 600 an den Stellen, die die `PWFILE`-Vorgaben erwarten. Die Owner-Antworten aus Task 1 legen den Umfang fest: Sprachfaelle auf der Box **ja**, DI-07-02 und DI-07-03 **beide**.

**Requirements:** MESS-01, MESS-02 und MESS-03 bleiben `Pending`. MESS-01 hat seine Kernzahl, aber der Vergleichslauf laeuft noch und der Bericht existiert nicht; abhaken darf sie der Plan, der die Zahlen zusammentraegt. `REQUIREMENTS.md` ist in keinem Commit dieses Plans.

## Known Stubs

Keine. Jede Zahl dieses Plans ist auf der Box gemessen, jede Rohdatei ist nicht leer, und die drei Urteilszeilen, an denen der Lauf haette scheitern sollen (`korpus-gleich`, `baumhash-gleich`, `grenze-gesetzt`), tragen alle drei ein `ja`.

Was fehlt, fehlt nicht als Stub, sondern als Laufzeit: Gesamtspitze, Laufzeit, `memory.events` ueber den ganzen Lauf, der p95 ueber den vollen Bestand, die zehn Sprachfaelle, die Seitenroute und die Rundenzaehlung. Alle sieben stehen in Plan 10-06 und brauchen das Ende des Laufs.

## Threat Flags

Keine neue Angriffsflaeche. Die Eintraege mit Disposition `mitigate`, und was dieser Lauf dazu belegt:

| Threat ID | Umsetzung, gemessen |
|-----------|---------------------|
| T-10-28 | `91-korpus.sh` lief VOR dem Indexaufbau, `korpus-gleich ja` gegen `bcbef9b2...` und 20.208.046.426 Byte |
| T-10-29 | `40b-baumhash.txt` traegt drei `baumhash:`-Zeilen und `baumhash-gleich ja`. Zusaetzlich ist der Beweis jetzt plattformunabhaengig, was er vorher nicht war |
| T-10-30 | `memory.max=2147483648` aus der cgroup zurueckgelesen, nach der Registrierung neu gesetzt, in `92-wechsel.txt` und erneut in `94-grundlast.txt` |
| T-10-31 | `nextcloud-instanzen 1` in `90-bestand.txt` und in `92-wechsel.txt`, letzteres in der folgenlosen Phase A vor `--rm-data`. Die Zaehlung selbst ist korrigiert, weil sie die zweite Instanz durchgelassen haette |
| T-10-32 | Die Trockenprobe des Lesers steht mit ihrer Ausgabe im Protokoll und traf eine echte Aufnahme: `2040 1653 264`, aus `backend` |
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
| Vier abgesetzte Prozesse laufen | Sampler, Statusbeobachter, Waechter, Meldekette, mit `pgrep` belegt |

## TDD Gate Compliance

Nicht anwendbar als Plan-Gate: der Plan traegt `type: execute` und keine Aufgabe ist mit `tdd="true"` ausgezeichnet. Die drei Korrekturen sind trotzdem mit ihrer Zusicherung committet, und zwei von ihnen sind gegen einen gestellten Fall gefahren, der ohne Box rot wird: die Instanzzaehlung gegen die neun echten Abbilder plus die zweite Instanz, und der Sortierschluessel gegen die zwei Namen, die den Unterschied ausgeloest haben.

---
*Phase: 10-vergleichsmessung-auf-der-aws-box*
*Completed: 2026-09-09 (Tasks 1 bis 3; Task 4 ist ein offener blockierender Checkpoint)*
