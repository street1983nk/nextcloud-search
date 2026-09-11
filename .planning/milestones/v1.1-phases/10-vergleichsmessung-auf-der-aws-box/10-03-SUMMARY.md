---
phase: 10-vergleichsmessung-auf-der-aws-box
plan: 03
subsystem: testing
tags: [measurement, shell-scripts, run-plan, cgroup, tree-hash, corpus-checksum, base-load, cold-start, p95, concurrency]

# Dependency graph
requires:
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "40b-baumhash.sh und .py aus Welle 1 als gerufener Beweisschritt, die Zeilenende-Regel fuer Messskripte und das Gate test_measurement_scripts.py, das die sieben neuen Skripte am Tag ihrer Entstehung prueft"
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: "der Digest von :dev aus Welle 2 (Manifestindex und arm64-Haelfte), die native arm64-Erwartung von 543,7 MB und der Nebenbefund DI-10-01 ueber leere Artefakte aus fehlenden Mountquellen"
  - phase: 06.1-launch-haertung
    provides: "60-bestand.sh, 61-wechsel.sh, 63-grundlast.sh, 64-spitze.sh und 67-nebenlaeufigkeit.sh als Vorlaeufer, deren Aufrufform und Parameter wortgleich uebernommen werden"
  - phase: 07-gemeinsame-embedding-engine
    provides: "01-grundlast-fein.py mit den fuenf benannten Posten, DI-07-02 als offene Frage nach dem Kaltstart und der Kaltstartwert 1.332,1 ms ueber den OCS-Weg"
provides:
  - "00-ablauf.md: der Lauf als Reihenfolge, dreizehn Schritte mit Rohdatei und Aussage, dreizehn Ablesestellen von memory.events, die Wartefristen mit ihren Uhren, vier Abbruchpfade und die offenen Handgriffe der Anfahrt"
  - "90-bestand.sh: der Bestand vor jedem Eingriff, mit mem=4G aus /proc/cmdline, Platz mit Zahl, state.db nur bei Existenz und Abbruch bei mehr als einer Nextcloud"
  - "91-korpus.sh: die Korpus-Pruefsumme als Skript mit Urteilszeile, vor dem Indexaufbau, Abbruch mit 6"
  - "92-wechsel.sh: der Abbildwechsel in zwei Phasen, mit gerufenem Baumhash-Beweis, Digestvergleich, --rm-data hinter einer Instanzzaehlung und harter Grenze aus der cgroup"
  - "93-nullstand.sh: der Nullstand aus vier Quellen mit Zahlen, findling:index --restart -n und 360 Sekunden gegen die langsamste Uhr"
  - "94-grundlast.sh: die MESS-01-Kernzahl in vier Teilen, Teil D mit der feinen Zerlegung von der Box und einer Pruefung gegen leere Artefakte"
  - "95-spitze.sh: die erste Suche als Ereignis in zwei Rollen, mit erzwungener Reihenfolge OOM-Beweis vor Neustart"
  - "97-nebenlaeufigkeit.sh: die p95-Reihe in den Parametern des Vorlaeufers, mit einer eigenen regression-Zeile je Stufe ueber der Baseline"
  - "96-oom-beweis.txt als Schnittstelle, die Plan 10-04 schreiben muss"
affects: [10-04, 10-05, 10-06, 10-07, box-lauf]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Urteil lebt in einer Datei unter $WORK und wird nach der tee-Pipeline gelesen, weil der Rueckgabewert einer Pipeline der von tee ist"
    - "Ein Schritt mit zerstoerendem Befehl wird in eine folgenlose Phase A und eine Phase B geteilt, damit jede Verweigerung vor dem ersten Eingriff steht"
    - "Eine Reihenfolge, die eingehalten werden muss, wird an eine Datei geknuepft und nicht an einen Satz im Kopf des Skripts"
    - "Ein Mount wird vor dem Lauf und seine Ausgabe nach dem Lauf geprueft, weil docker fuer eine fehlende Mountquelle ein leeres Verzeichnis anlegt"
    - "Jedes Leseskript wird trocken gegen das echte Schema gefahren, bevor es scharfgestellt wird, auch wenn das Schema ein Antwort-JSON ist"

key-files:
  created:
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/00-ablauf.md
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/90-bestand.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/91-korpus.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/92-wechsel.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/93-nullstand.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/94-grundlast.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/95-spitze.sh
    - docs/measurements/2026-09-vergleichsmessung-m7g/skripte/97-nebenlaeufigkeit.sh
  modified: []

key-decisions:
  - "Jedes Urteil wird in eine Datei unter $WORK geschrieben und nach der tee-Pipeline gelesen. Der Plan verlangt den { ... } | tee-Block UND einen Abbruch mit Rueckgabewert; ein exit im Block verlaesst nur die Subshell, und der Schritt waere gruen weitergelaufen"
  - "92-wechsel.sh laeuft in zwei Phasen. Die Verweigerungen (Instanzzahl, Baumhash, sauberer Arbeitsbaum) muessen VOR --rm-data greifen, und nach dem Block, der --rm-data enthaelt, ist jede Pruefung zu spaet. Phase A ist folgenlos, ihre Ausgabe wandert in dieselbe Rohdatei"
  - "95-spitze.sh in der Rolle nachher verweigert den Neustart, solange 96-oom-beweis.txt fehlt. Ein Satz im Kopf ist eine Erinnerung; T-10-17 handelt von einer Reihenfolge, die um drei Uhr morgens gebrochen wird. Die Datei ist eine Variable mit Vorgabe, also eine benannte Schnittstelle zu Plan 10-04"
  - "Die einzelne Suche ist eine Anfrage und nicht drei. 64-spitze.sh fuhr seine erste Suche mit rounds 3, also trug die erste den Kaltstart und die anderen zwei verwaesserten ihn. DI-07-02 fragt nach dem Kaltstart, und die Stufenreihe danach behaelt die Parameter des Vorlaeufers unveraendert"
  - "Teil D prueft Mountquelle und Ausgabe. Ein docker run legt fuer eine fehlende Mountquelle ein leeres Verzeichnis an, das Werkzeug schreibt eine leere Datei, der Schritt bleibt gruen: genau so ist chars-per-token-prose.txt 0 Byte gross geworden (DI-10-01), und es ist dieselbe Fehlerklasse wie der leere Baumhash, den diese Phase reparieren soll"
  - "Der Digestvergleich nimmt beide Gestalten an, Manifestindex und arm64-Haelfte, und ist ein benannter Befund statt eines Abbruchs. Der Pfadfilter von docker.yml reicht in backend/**, also verschiebt ein Commit mit einer Testdatei den Digest ohne eine Zeile im Abbild zu aendern. Der Vergleich, der traegt, ist der Baumhash"
  - "Die Regression-Zeile bekommt ein benanntes Rauschband von fuenf Prozent. Der Plan verlangt eine Zeile fuer jede Stufe, die schlechter ist; ohne Band waere eine Abweichung von 1,8 Prozent im Bericht als Regression gelesen worden"
  - "00-ablauf.md traegt echte Umlaute, die Skripte englische Kommentare. Der Plan verlangt deutsche Prosa mit echten Umlauten, die Nachbardateien unter docs/measurements halten es so, und jede Zeichenkette in Backticks bleibt ASCII"
  - "MESS-01 und MESS-03 bleiben Pending, obwohl das Frontmatter des Plans sie fuehrt: dieser Plan hat null Box-Minuten gekostet, keine Rohdatei erzeugt und keinen Bericht geschrieben"

patterns-established:
  - "Zwei Phasen in einem Schritt, wenn eine Verweigerung vor einem zerstoerenden Befehl liegen muss, und die Ausgabe der ersten Phase wandert in die Rohdatei der zweiten"
  - "Eine Reihenfolge zwischen zwei Skripten wird an eine Datei geknuepft, deren Name eine Variable mit Vorgabe ist"
  - "Ein Auswertungsblock wird gegen ein nachgebautes Antwort-JSON gefahren, samt des Falls, in dem keine Anfrage beantwortet wurde"

requirements-completed: []
requirements-touched: [MESS-01, MESS-03]

# Metrics
duration: 28min
completed: 2026-09-09
---

# Phase 10 Plan 03: Der Ablaufplan und das Skriptset vor dem Volllauf Summary

**Der Lauf ist als Reihenfolge beschrieben, bevor er stattfindet, und die zwei Feststellungen, die ihn retten koennen, bevor er 19 Stunden kostet, sind Skripte mit Urteilszeile und Rueckgabewert statt Handgriffe mit Erinnerung.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-09-09T08:05:00Z
- **Completed:** 2026-09-09T08:33:00Z
- **Tasks:** 3 von 3
- **Files modified:** 8 (alle neu)
- **Box-Minuten:** 0, wie geplant
- **Runner-Minuten:** 0

## Accomplishments

- **Der Lauf hat eine Reihenfolge, und sie ist nachlesbar:** `00-ablauf.md` fuehrt dreizehn Schritte, jeder mit Skriptdatei, Rohdatei und der Aussage, an der er haengt, dazu dreizehn Ablesestellen von `memory.events` als eigene Liste, vier Wartefristen mit den Uhren, gegen die sie bemessen sind, vier Abbruchpfade und die drei Handgriffe, die `aws_box.sh start` ausdruecklich offen laesst.
- **Die zwei Rettungsanker sind Skripte:** `91-korpus.sh` faellt mit 6 aus, bevor der Indexaufbau beginnt, wenn die Listen-Pruefsumme nicht `bcbef9b2...` oder die Bytezahl nicht 20.208.046.426 ist, und nennt die x86-Zeile `c03a8803...` ausdruecklich als den falschen Vergleichswert. `92-wechsel.sh` faellt mit 4 aus, wenn `40b-baumhash.txt` nicht drei `baumhash:`-Zeilen und `baumhash-gleich ja` traegt.
- **Der Beweisschritt wird gerufen, nicht nachgebaut**, und er erbt Abbild und Ausgabeort ausdruecklich per `export`. Ohne das haetten beide Skripte nur deshalb dasselbe Abbild gelesen, weil sie dieselbe Vorgabe tragen.
- **Der zerstoerende Befehl steht hinter drei Verweigerungen, und alle drei greifen davor:** `92-wechsel.sh` laeuft in einer folgenlosen Phase A (Instanzzahl, Digest, Baumhash, info.xml-Kopie, `git status --porcelain`) und einer Phase B, die die Box aendert. Mehr als eine Nextcloud endet mit 5, ein unsauberer Arbeitsbaum mit 8, eine harte Grenze ungleich `2147483648` mit 9.
- **Die Reihenfolge, an der DI-07-02 haengt, ist erzwungen statt erinnert:** `95-spitze.sh nachher` verweigert den `docker restart` mit 12, solange `96-oom-beweis.txt` fehlt, weil ein Neustart `memory.peak` und `memory.events` zuruecksetzt und der Beweis danach aus dem falschen Grund null lesen wuerde.
- **Die Grundlast hat einen vierten Teil, und er kann nicht leer bleiben:** Teil D fahrt `01-grundlast-fein.py` unter `--network none` im Abbild, prueft die Mountquelle vorher und die Ausgabe nachher auf `00-leerer-prozess` und `12c-zweiter-chunkerlauf`. Das ist die Lehre aus DI-10-01, angewandt bevor sie ein zweites Mal kostet.
- **Kein Regressionsschatten:** ganze Suite 1913 passed / 15 skipped gegen die Grundlinie 1878 / 15, also genau die 35 neuen Zusicherungen der sieben Skripte (fuenf je Datei) und keine gebrochene alte. `ruff check`, `ruff format --check`, `pyright` und `vulture` ohne Befund.

## Task Commits

1. **Task 1: Der Ablaufplan, der Bestand und die Korpus-Pruefsumme** , `9d0e2a0` (feat)
2. **Task 2: Abbildwechsel mit Baumhash-Beweis, und der Nullstand** , `8107b0c` (feat)
3. **Task 3: Grundlast, die erste Suche als Ereignis, und die Nebenlaeufigkeitsreihe** , `9a940c7` (feat)
4. **Nachtrag zu Task 2:** `22c9c9b` (fix) , der Beweisschritt erbt Abbild und Ausgabeort per `export`

## Files Created

| Datei | Was sie tut, und was sich gegen den Vorlaeufer geaendert hat |
|---|---|
| `00-ablauf.md` | Der Ablaufplan. Dreizehn Schritte, dreizehn Ablesestellen, vier Wartefristen, vier Abbruchpfade, die Anfahrt mit A-Record und seinen zwei Rueckfaellen, und die Regel "genau eine Nextcloud auf dieser Box". Deutsche Prosa mit echten Umlauten. |
| `90-bestand.sh` | Nach `60-bestand.sh`. Neu: `state.db` wird nur gelesen, wenn sie existiert, und ihre Abwesenheit ist eine Beobachtung mit Datum; `mem=4G` kommt aus `/proc/cmdline` mit Urteilszeile; der Platz auf dem Datentraeger steht mit Zahl da, samt Abbildliste und `docker system df`; `docker ps` zaehlt die Nextcloud-Instanzen und mehr als eine endet mit 5. |
| `91-korpus.sh` | Ruft `44-korpus-pruefsumme.py` unveraendert, vergleicht Pruefsumme und Bytezahl, schreibt `korpus-gleich ja` oder `nein`, faellt mit 6 (Abweichung) oder 7 (keine Lesung) aus. Der Kopf sagt, warum die x86-Zeile falsch ist und warum der Schritt vor dem Indexaufbau steht. |
| `92-wechsel.sh` | Nach `61-wechsel.sh`, in zwei Phasen. Ruft `40b-baumhash.sh`, prueft dessen Rohdatei, haelt den Digest gegen Index und arm64-Haelfte aus Welle 2, macht die info.xml-Kopie ausserhalb des Arbeitsbaums und prueft ihn danach, spielt die PHP-Haelfte nach `custom_apps/findling` ein, registriert, setzt die harte Grenze und liest sie aus der cgroup zurueck. |
| `93-nullstand.sh` | Neu in dieser Form. Vier Quellen mit Zahlen, dann `findling:index --restart -n`, 360 Sekunden gegen die langsamste Uhr, dann der Arbeitsvorrat als Urteil. Kein Vorrat endet mit 10 und verweist auf Annahme A2. |
| `94-grundlast.sh` | Nach `63-grundlast.sh`, Teile A, B und C wortgleich mit unveraenderten Hilfsskripten. Neu: Teil D mit `01-grundlast-fein.py` unter `--network none`, samt Pruefung von Mountquelle und Ausgabe, und die Plausibilitaetszeile gegen 691,8 MB, 693,4 MB und die Erwartung 118 bis 150 MB. |
| `95-spitze.sh` | Nach `64-spitze.sh`, mit Pflichtrolle `vorher` oder `nachher` im Rohdateinamen. Genau eine Suche als Ereignis, dann die Stufen 1, 4 und 8. In der Rolle `nachher`: Verweigerung ohne OOM-Beweis, dann Neustart, dann die Kaltstartzeile gegen die 1,5-s-Decke und gegen 1.332,1 ms mit Marge. |
| `97-nebenlaeufigkeit.sh` | Nach `67-nebenlaeufigkeit.sh`, in Aufbau und Parametern wortgleich: fuenf Stufen, zehn Runden, 410 Anfragen, 20 Sekunden Pause. Neu: die Tabelle nennt die Baseline-Spalte, und jede Stufe ueber der Baseline bekommt eine eigene `regression`-Zeile mit Prozentsatz und Rauschband. |

## Decisions Made

Die tragenden Entscheidungen stehen im Frontmatter. Drei verdienen den Fliesstext:

**Warum ein Urteil nicht in der Pipeline leben kann.** Der Plan verlangt zweierlei, das sich beisst: die Ausgabe in einem `{ ... } 2>&1 | tee "$ZIEL"`-Block, und einen Abbruch mit einem Rueckgabewert ungleich null. Weil die geschweiften Klammern vor einer Pipe in einer Subshell laufen, verlaesst ein `exit` darin nur diese Subshell; der Schritt haette weitergemacht und mit 0 geendet, und die Verweigerung waere eine Zeile in der Rohdatei gewesen, die niemand liest. Genau die Fehlerart, die diese Phase an ihren Vorlaeufern behebt. Also schreibt jeder Schritt sein Urteil in eine Datei unter `$WORK` und liest sie nach der Pipeline zurueck. Vier der sieben Skripte enden auf diesem Weg mit einem eigenen Code (5, 6 und 7, 4 und 8 und 9, 10, 11, 12), und jeder Code steht im Kopf seiner Datei.

**Warum `92-wechsel.sh` zwei Phasen hat.** Die drei Verweigerungen dieses Schrittes muessen vor `--rm-data` greifen, nicht danach. Eine Pruefung hinter dem Block, der `--rm-data` enthaelt, kommt zu spaet: das Volumen ist dann weg, und bei mehr als einer Nextcloud waere es das falsche. Phase A pullt das Abbild, liest den Digest, ruft den Baumhash-Beweis, baut die info.xml-Kopie und prueft den Arbeitsbaum, und keiner dieser Schritte aendert etwas. Erst nach den drei Verweigerungen beginnt Phase B. Die Ausgabe von Phase A wandert per `cat` in die Rohdatei von Phase B, damit eine Datei den ganzen Schritt traegt.

**Warum die einzelne Suche eine Anfrage ist und nicht drei.** `64-spitze.sh` nennt seinen Abschnitt "the very first semantic search of this container start, alone" und fahrt ihn mit `--rounds 3`, also drei Anfragen. Die erste trug den Kaltstart, die anderen zwei liefen gegen ein geladenes Modell und haben den Wert verwaessert. Fuer die Speicheraussage der Nachmessung war das gleichgueltig, weil die Gewichte bei der ersten Anfrage ankommen; fuer DI-07-02 ist es der Unterschied zwischen der Frage und ihrer Antwort. Die Stufenreihe danach behaelt `--rounds 3` und bleibt damit Zeile fuer Zeile vergleichbar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ein `exit` im tee-Block haette keinen Schritt abgebrochen**

- **Found during:** Task 1, beim ersten Entwurf von `90-bestand.sh`
- **Issue:** Der Plan verlangt die Ausgabe im `{ ... } 2>&1 | tee "$ZIEL"`-Block und gleichzeitig einen Abbruch mit Rueckgabewert ungleich null. Beides zusammen geht nicht direkt: die Klammern vor einer Pipe laufen in einer Subshell, ein `exit` darin beendet nur diese, und der Rueckgabewert der Pipeline ist der von `tee`, also 0. Jede Abbruchbedingung des Plans waere eine Zeile in der Rohdatei geblieben und kein Abbruch.
- **Fix:** Jedes Urteil wird im Block in eine Datei unter `$WORK` geschrieben und nach der Pipeline gelesen; dort steht der `exit`. Bei `92-wechsel.sh` kam die Teilung in zwei Phasen hinzu, weil drei der Verweigerungen vor `--rm-data` liegen muessen.
- **Files modified:** alle sieben Shellskripte
- **Verification:** `sh -n` ohne Befund; die Urteilsdateien und ihre Auswertung stehen in jedem Skript hinter der Pipeline
- **Committed in:** `9d0e2a0`, `8107b0c`, `9a940c7`

**2. [Rule 2 - Missing critical functionality] Die Rolle `nachher` verweigert den Neustart ohne den OOM-Beweis**

- **Found during:** Task 3
- **Issue:** Der Plan sagt, der Neustart fuer die Rolle `nachher` muesse "ausdruecklich NACH dem OOM-Beweis" stattfinden, und verlangt den Satz im Kopf der Datei. Ein Satz im Kopf ist eine Erinnerung. T-10-17 beschreibt genau den Fall, in dem sie nicht gelesen wird, und ein Neustart setzt `memory.peak` und `memory.events` zurueck: der Beweis danach liest null, weil er geloescht wurde, und nicht, weil nichts passiert ist. Das ist unheilbar, sobald es passiert ist.
- **Fix:** `95-spitze.sh` in der Rolle `nachher` prueft `96-oom-beweis.txt` und endet mit 12, wenn die Datei fehlt oder leer ist. Der Name ist eine Variable mit Vorgabe, also eine benannte Schnittstelle; `00-ablauf.md` fuehrt sie in Schritt 7 und in Schritt 9.
- **Files modified:** `95-spitze.sh`, `00-ablauf.md`
- **Verification:** `sh -n` ohne Befund; der Zweig liegt vor dem `docker restart` und vor jeder Messung
- **Committed in:** `9a940c7`

**3. [Rule 2 - Missing critical functionality] Teil D prueft Mountquelle und Ausgabe, statt eine leere Datei zu erzeugen**

- **Found during:** Task 3, aus dem Nebenbefund DI-10-01 der Welle 2
- **Issue:** Der Plan verlangt Teil D "so wie `measure.yml` es tut". Genau so hat `measure.yml` eine 0-Byte-Datei erzeugt: der Mount zeigte auf ein verschobenes Verzeichnis, `docker run` legt fuer eine fehlende Mountquelle ein leeres Verzeichnis an, das Werkzeug schreibt eine leere Datei, und der Schritt bleibt gruen. Ein Teil D, der die Zerlegung in fuenf Posten liefern soll und eine leere Ausgabe hinterlaesst, ist dieselbe Fehlerklasse wie der leere Baumhash, den diese Phase reparieren soll.
- **Fix:** Die Mountquelle wird vor dem Lauf geprueft, die Ausgabe danach auf `00-leerer-prozess` und `12c-zweiter-chunkerlauf`, und ein fehlender Teil D endet mit 11. Beide Zweige schreiben `feinmessung-vollstaendig ja` oder `nein` in die Rohdatei.
- **Files modified:** `94-grundlast.sh`
- **Verification:** `sh -n` ohne Befund; der Kopf nennt DI-10-01 als Grund
- **Committed in:** `9a940c7`

**4. [Rule 1 - Bug] Beide Auswertungsbloecke waeren an einer Stufe ohne beantwortete Anfrage mit einem KeyError gestorben**

- **Found during:** Task 3, beim Trockenlauf gegen ein nachgebautes Antwort-JSON
- **Issue:** `search_load.py` schreibt `p50_ms`, `p95_ms`, `max_ms` und `p95_within_budget` **nur**, wenn mindestens eine Anfrage beantwortet wurde. Eine Stufe, in der alles fehlschlaegt, ist der interessanteste Fall der ganzen Reihe, und sie haette die Tabelle mit einem Traceback beendet: die Rohdatei traegt dann einen Abschnittstitel und darunter nichts, also genau die Gestalt, die diese Phase an ihren Vorlaeufern behebt. `67-nebenlaeufigkeit.sh` traegt denselben latenten Fehler; er bleibt ausserhalb dieses Plans, weil seine Rohdaten daneben liegen.
- **Fix:** Beide Bloecke pruefen den Schluessel, nennen den Fall samt `failure_kinds` und laufen weiter. Gefunden wurde er, weil beide Bloecke gegen nachgebaute Berichte im echten Schema trocken gefahren wurden, samt der leeren Stufe und der fehlenden Datei (Fallstrick 8).
- **Files modified:** `95-spitze.sh`, `97-nebenlaeufigkeit.sh`
- **Verification:** Trockenlauf: fuenf Stufen, davon eine ohne Antwort, ergibt die Tabelle plus zwei `regression`-Zeilen; der Kaltstartblock liefert in allen drei Faellen (Antwort, keine Antwort, fehlende Datei) eine Zeile und Rueckgabewert 0
- **Committed in:** `9a940c7`

**5. [Rule 2 - Missing critical functionality] Der Beweisschritt erbt Abbild und Ausgabeort ausdruecklich**

- **Found during:** Nachtrag zu Task 2, beim Nachlesen der Aufrufkette
- **Issue:** `92-wechsel.sh` und `40b-baumhash.sh` tragen dieselben Vorgaben fuer `IMAGE` und `OUT`, also stimmten sie ueberein, solange niemand etwas ueberschreibt. Eine Ueberschreibung, die die Umgebung nicht erreicht, haette den Baumhash gegen ein Abbild belegt und gegen ein anderes registriert: T-10-13 mit einem gruenen Schritt davor.
- **Fix:** `export IMAGE OUT REPO` unmittelbar vor dem Aufruf, mit der Begruendung als Kommentar an derselben Stelle.
- **Files modified:** `92-wechsel.sh`
- **Verification:** `sh -n` ohne Befund; Gate 121 passed
- **Committed in:** `22c9c9b`

**6. [Rule 1 - Bug] MESS-01 und MESS-03 wurden nicht abgehakt, obwohl das Frontmatter sie fuehrt**

- **Found during:** Zustands-Update nach Task 3
- **Issue:** Das Frontmatter des Plans nennt `requirements: [MESS-01, MESS-03]`. MESS-01 verlangt einen Vergleichslauf auf der Box, der die RSS-Ersparnis belegt, MESS-03 den Bericht in `docs/measurements` mit der Struktur des v1.0-Berichts. Dieser Plan hat acht Dateien geschrieben, die Box nicht angefasst, keine Rohdatei erzeugt und keinen Bericht. Derselbe Fehlgriff ist in Welle 1 passiert und zurueckgenommen worden (Deviation 7 der 10-01-SUMMARY) und in Welle 2 vermieden worden (Deviation 4 der 10-02-SUMMARY).
- **Fix:** `requirements.mark-complete` nicht aufgerufen. `REQUIREMENTS.md` bleibt unveraendert, beide Kennungen stehen weiter auf `Pending`, und im Frontmatter dieser Zusammenfassung ist `requirements-completed` leer.
- **Files modified:** keine (`.planning/REQUIREMENTS.md` ausdruecklich nicht angefasst)
- **Verification:** `grep MESS-0 .planning/REQUIREMENTS.md` zeigt drei offene Kaestchen und drei `Pending`-Zeilen; `REQUIREMENTS.md` steht in keinem Commit dieses Plans
- **Committed in:** dieser Metadaten-Commit

**7. [Rule 1 - Bug] Drei Zustandsbefehle des SDK haben wieder falsche oder leere Werte geschrieben**

- **Found during:** Zustands-Update
- **Issue:** Wie in Welle 2: `state.add-decision` schrieb die drei Entscheidungen mit dem Vermerk `[Phase ?]` davor, `state.update-progress` meldete "Progress field not found in STATE.md" und liess `completed_plans` auf 19, und `state.record-metric` nahm zwar die Flags, aber die Dauer war zu diesem Zeitpunkt noch geschaetzt.
- **Fix:** Die drei Vermerke auf `[Phase 10]` gesetzt, `completed_plans` auf 20, die Dauer in der Metrik auf die gemessenen 28 Minuten korrigiert und die Zeile "Naechster Schritt" auf Welle 4 samt der Schnittstelle `96-oom-beweis.txt` geschrieben.
- **Files modified:** `.planning/STATE.md`
- **Verification:** `grep "Phase ?"` ohne Treffer, `completed_plans: 20`, `stopped_at: Completed 10-03-PLAN.md`, `| Phase 10 P03 | 28min | 3 tasks | 8 files |`
- **Committed in:** dieser Metadaten-Commit

### Kleinere Abweichungen, ohne eigene Regel

- **Die einzelne Suche ist eine Anfrage statt drei** (`--concurrency 1 --rounds 1` gegen `--rounds 3` beim Vorlaeufer). Begruendet im Fliesstext und im Kopf der Datei; die Stufenreihe ist unveraendert.
- **Die `regression`-Zeile nennt ein Rauschband.** Der Plan verlangt eine Zeile fuer jede Stufe, die schlechter ist als die Baseline. Das ist so umgesetzt, und jede Zeile sagt zusaetzlich, ob die Abweichung ueber fuenf Prozent liegt. Ohne diesen Zusatz waeren die 1,8 Prozent des Trockenlaufs im Bericht als Regression gelesen worden.
- **Das Abschlusswort von `95-spitze.sh` ist `95-SPITZE-FERTIG rolle=<rolle>`** und nicht `95-SPITZE-<ROLLE>-FERTIG`, damit die feste Zeichenkette greppbar bleibt und beide Laeufe trotzdem unterscheidbar sind.
- **`00-ablauf.md` traegt echte Umlaute.** Der erste Entwurf war in `ae/oe/ue` geschrieben wie die Skriptkoepfe. Der Plan verlangt "deutsche Prosa mit echten Umlauten", die Nachbardateien unter `docs/measurements` fuehren sie, und das Gate deckt `.md` nicht. Umgestellt wurden nur Prosawoerter; jede Zeichenkette in Backticks und jeder Dateiname (`97-nebenlaeufigkeit.sh`, `98-sprachfaelle.sh`) sind unveraendert ASCII.
- **Das Passwort steht als Dateipfad mit `$HOME`** (`PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"`) und nicht als der Pfad der Box, weil `MACHINE_SHAPES` die Zeichenfolge `/home/` im Code verbietet. Der Wert wandert in `FINDLING_LOAD_PASSWORD` und wird ueber `--password-env` uebergeben, also nie in ein Argument.
- **`90-bestand.sh` nennt zusaetzlich die Groesse des Korpusverzeichnisses.** Nicht verlangt, aber es ist die Zahl, um die Annahme A3 geht, und sie kostet ein `du -sh`.
- **`92-wechsel.sh` faellt beim `unregister` auf `--force` zurueck.** Am 07.09. war das noetig, weil die AppAPI-Zeile ohne Container zurueckblieb (Befund arm64-5 in `docs/install-check.md`). Die Leere des Volumens wird nicht in Phase B behauptet, sondern in Schritt 4 mit Zahlen belegt: AppAPI legt das Volumen beim Registrieren sofort neu an, also ist die Auflistung zwischen `unregister` und `register` eine Beobachtung und kein Urteil.

---

**Total deviations:** 7 auto-fixed (3x Rule 1 Bug, 4x Rule 2 fehlende kritische Funktionalitaet) plus sieben kleinere Abweichungen ohne eigene Regel
**Impact on plan:** Kein Scope Creep, keine Fremdabhaengigkeit, kein Paket installiert, `backend/uv.lock` unveraendert. Fuenf der sieben drehen sich um denselben Punkt: eine Abbruchbedingung, die nicht abbricht, und eine Rohdatei, die leer bleiben kann, sind keine Pruefungen, sondern Zeilen, die jemand ueberliest. Genau die Fehlerart, deren Reparatur der Gegenstand dieser Phase ist.

## Issues Encountered

**Der Rueckgabewert einer Pipeline gehoert `tee`.** Das ist die eine Erkenntnis, die die Gestalt aller sieben Skripte bestimmt hat, und sie war nicht offensichtlich, weil die Vorlaeufer keinen Abbruch kennen: `60-bestand.sh` bis `67-nebenlaeufigkeit.sh` haben keine einzige Bedingung, die einen Schritt beendet. Diese sieben haben zehn. Deshalb liegt jedes Urteil in einer Datei und nicht in einem `exit`, und deshalb ist `92-wechsel.sh` zweigeteilt.

**Die Zahl, gegen die `95-spitze.sh` seine Kaltstartzeit haelt, steht in PHP und nicht in Python.** `search_load.py` traegt `REQUEST_TIMEOUT_SECONDS = 30.0`, das ist das Timeout des Messwerkzeugs. Die 1,5-Sekunden-Decke, nach der DI-07-02 fragt, ist `ExAppService::REQUEST_TIMEOUT_SECONDS = 1.5` in `php/lib/Service/ExAppService.php`, und daneben steht `PAGE_REQUEST_TIMEOUT_SECONDS` mit demselben Wert fuer die Anzeigeseite. Das Skript nennt die PHP-Konstante mit Klassennamen, damit die Verwechslung im Bericht nicht moeglich ist.

**`occ findling:index` liefert zwei der vier Nullstandsquellen aus einem Aufruf.** Der Befehl gibt den Arbeitsvorrat und die Endzustaende aus `oc_findling_file_state` in zwei Bloecken derselben Ausgabe. Zweimal zu fragen haette zwei Antworten erlaubt, die sich widersprechen, also wird einmal gefragt und die Ausgabe zweimal gelesen, mit einem Satz, der genau das sagt. Der Parser ist trocken gegen die Ausgabegestalt gefahren, einmal mit Vorrat und einmal mit null.

**`gsd-sdk query state.*` verhaelt sich wie in Welle 2 notiert.** Flags statt Positionsargumente, `[Phase ?]` vor jeder Entscheidung, `update-progress` findet das Feld nicht, und `roadmap.update-plan-progress` laeuft durch, ohne das Kaestchen zu setzen, weil die Phase-10-Plaene als Kaestchenliste stehen. Alles von Hand nachgezogen, wie in Welle 2.

## User Setup Required

None. Der Plan hat keine Cloud-Ressource angefasst, die Box nicht gestartet und keine Runner-Minute verbraucht.

## Next Phase Readiness

**Bereit fuer Welle 4.** Was diese Welle hinterlaesst:

- **Eine Schnittstelle, die Plan 10-04 einhalten muss:** der Waechter schreibt den OOM-Beweis in eine eigene Rohdatei `96-oom-beweis.txt`. Ohne sie bricht `95-spitze.sh nachher` mit 12 ab. Der Name ist die Variable `OOM_BEWEIS` mit Vorgabe, also anpassbar, aber die Datei muss es geben. `00-ablauf.md` fuehrt sie in Schritt 7 und Schritt 9.
- **Die Zeilen, die Plan 10-04 ergaenzt:** die Schritte 96, 98, 99 und 99b stehen in `00-ablauf.md` mit "Plan 10-04" in der Spalte der Rohdatei. Sie brauchen ihre Rohdateinamen und, wo sie eine Ablesestelle von `memory.events` sind, die Nummern 8, 9, 10 und 13 aus Abschnitt 3.
- **Zehn Rueckgabewerte, die im Bericht auftauchen koennen:** 4 Baumhash, 5 mehr als eine Nextcloud, 6 Korpus, 7 keine Lesung, 8 unsauberer Arbeitsbaum, 9 harte Grenze, 10 kein Arbeitsvorrat, 11 leerer Teil D, 12 fehlender OOM-Beweis, und 2 fuer eine unbekannte Rolle. Jeder steht im Kopf seiner Datei.
- **Das Muster fuer die Skripte der Welle 4:** Urteil in eine Datei, Auswertung hinter der Pipeline, und wo ein zerstoerender Befehl im Spiel ist, zwei Phasen.

**Was dieser Plan ausdruecklich nicht getan hat:** keine Zeile der Vorlaeuferskripte geaendert, kein Schrittname der Grundlast-Aufschluesselung umbenannt, kein Hilfsskript angefasst. `44-korpus-pruefsumme.py`, `49b-gewichte.py`, `52-woher-die-grundlast.py` und `01-grundlast-fein.py` werden gerufen, wie sie sind. Der latente KeyError in `67-nebenlaeufigkeit.sh` bleibt stehen, weil seine Rohdaten daneben liegen und eine Korrektur ihre Herkunft verwischen wuerde.

**Ein Hinweis, der keine Aufgabe ist:** `.gitattributes` deckt `docs/measurements/**/skripte/*.py` und global `*.sh`, aber nicht `*.md`. `00-ablauf.md` ist die erste Markdown-Datei unter `skripte/` und bekommt in einem Windows-Checkout Wagenrueckläufe. Sie wird gelesen und nie ausgefuehrt, und das Gate deckt `.py` und `.sh`; deshalb steht das hier als Beobachtung und nicht als offener Punkt.

## Known Stubs

Keine im Sinne von unverdrahteten Daten. Die sieben Skripte sind vollstaendig und lokal mit `sh -n` geprueft; ihre Docker-, `occ`- und cgroup-Haelften koennen ohne Box nicht gefahren werden, und das ist keine Auslassung, sondern der Gegenstand der Welle 5. Was ohne Box pruefbar war, ist geprueft: die vier eingebetteten Python-Bloecke uebersetzen, und die zwei Auswertungsbloecke sind gegen nachgebaute Antwort-JSONs im echten Schema trocken gefahren, samt der Stufe ohne beantwortete Anfrage und der fehlenden Datei.

Die vier Zeilen von `00-ablauf.md`, die "Plan 10-04" in der Rohdatenspalte tragen, sind kein Stub, sondern der ausdrueckliche Auftrag des Plans: eine Reihenfolge ist nur als ganze eine Reihenfolge, und Welle 4 ergaenzt die Namen.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Registers. Die neun Eintraege mit Disposition `mitigate`:

| Threat ID | Umsetzung |
|-----------|-----------|
| T-10-11 | `90-bestand.sh` und `92-wechsel.sh` zaehlen die Nextcloud-Instanzen aus `docker ps` und enden mit 5 bei mehr als einer; die Zaehlung in `92-wechsel.sh` liegt in der folgenlosen Phase A, also vor `--rm-data`; `00-ablauf.md` fuehrt die Regel "genau eine Nextcloud auf dieser Box" im Abschnitt der Anfahrt |
| T-10-12 | `docker update` nach der Registrierung, `memory.max` und `memory.swap.max` aus der cgroup gelesen, Erwartungswert `2147483648`, Abbruch mit 9; `94-grundlast.sh` setzt und liest die Grenze erneut, bevor es die erste Zahl nimmt |
| T-10-13 | `40b-baumhash.sh` wird gerufen, seine Rohdatei auf drei verankerte `baumhash:`-Zeilen und `baumhash-gleich ja` geprueft, Abbruch mit 4; Abbild und Ausgabeort werden per `export` uebergeben, damit Beweis und Registrierung dasselbe Abbild betreffen |
| T-10-14 | `49b-gewichte.py` und `52-woher-die-grundlast.py` werden per `docker cp` unveraendert in den Container gebracht und gerufen; kein Schrittname ist umbenannt, und der Kopf von `94-grundlast.sh` nennt die Schrittnamen ausdruecklich als Vergleichsschluessel |
| T-10-15 | Das Passwort kommt aus einer Datei in eine Umgebungsvariable und wird mit `--password-env` uebergeben; das Gate aus Welle 1 prueft alle sieben Dateien auf `--password `, `--password=` und die Kurzform hinter einem Programm, das ein Passwort so nimmt |
| T-10-16 | `95-spitze.sh` verlangt die Rolle als Pflichtargument, lehnt jeden anderen Wert mit 2 ab, bildet alle Rohdateinamen daraus und nennt die Rolle in der Kaltstartzeile; nur die Rolle `nachher` traegt den Satz, dass dies die Antwort auf DI-07-02 ist |
| T-10-17 | Erzwungen statt erinnert: ohne `96-oom-beweis.txt` endet `95-spitze.sh nachher` mit 12, bevor der `docker restart` abgesetzt wird; `00-ablauf.md` fuehrt die Reihenfolge in Schritt 7 und Schritt 9 |
| T-10-18 | Die info.xml-Kopie entsteht unter `mktemp -d`, wird als `92-info-box.xml` gesichert, und `git status --porcelain backend/appinfo/info.xml` muss leer sein, sonst Abbruch mit 8 |
| T-10-SC | Kein Paket installiert. Die Skripte rufen ausschliesslich Werkzeuge des Repos und der Box; die eingebetteten Python-Bloecke importieren nur `json`, `sqlite3`, `pathlib`, `sys` und `datetime`. `backend/uv.lock` unveraendert |

Zusaetzlich zur Bedrohungstabelle, weil es die Grenze "Messskript zur cgroup" betrifft: keine der acht Dateien enthaelt `docker stats` oder eine andere Speicherzahl aus dem Docker-Klienten. Jede Zahl kommt aus `/sys/fs/cgroup/system.slice/docker-<CID>.scope/`, und `95-spitze.sh` loest die Container-Kennung nach dem Neustart neu auf, damit der Pfad nicht auf eine alte cgroup zeigt.

## Self-Check: PASSED

| Geprueft | Ergebnis |
|----------|----------|
| Alle acht Dateien aus `files_modified` liegen auf der Platte | achtmal `FOUND` |
| Alle vier Commits in `git log` | `9d0e2a0`, `8107b0c`, `9a940c7`, `22c9c9b` |
| `git diff --name-only 7da2111 HEAD` | genau die acht Dateien des Plans, keine neunte |
| Loeschungen in den vier Commits | keine (`--diff-filter=D` leer) |
| `sh -n` ueber alle sieben Shellskripte | ohne Befund |
| Zusicherung Task 1 | `ok` |
| Zusicherung Task 2 | `ok` |
| Zusicherung Task 3 | `ok` |
| Die vier eingebetteten Python-Bloecke | uebersetzen (`ast.parse`) |
| Trockenlauf der Nebenlaeufigkeitstabelle | fuenf Stufen, eine ohne Antwort benannt, zwei `regression`-Zeilen mit Rauschband |
| Trockenlauf der Kaltstartzeile | Antwort, keine Antwort und fehlende Datei, jeweils eine Zeile und Rueckgabewert 0 |
| Trockenlauf des Arbeitsvorrat-Parsers | 1239 aus einer gefuellten Ausgabe, 0 aus einer leeren |
| `pytest tests/test_measurement_scripts.py -q` | 121 passed (86 vor diesem Plan, 35 neue aus sieben Dateien) |
| `pytest -q` (ganze Suite) | 1913 passed / 15 skipped (Grundlinie 1878 / 15) |
| `ruff check .`, `ruff format --check .` in `backend/` | All checks passed, 120 files already formatted |
| `ruff check` und `ruff format --check` ueber das Laufverzeichnis | All checks passed, 2 files already formatted |
| `pyright` | 0 errors, 0 warnings, 0 informations |
| `vulture src tests --min-confidence 80` | ohne Befund |
| Wagenruecklauf in den acht Dateien | keiner |
| Em-Dash oder En-Dash in den acht Dateien und in dieser Zusammenfassung | keiner |
| `docker stats` in einer der acht Dateien | kein Treffer |
| Maschinenpfad in den sieben Skripten | `machine_shapes_in_code` liefert `[]` fuer alle sieben |
| `.planning/REQUIREMENTS.md` unveraendert | nicht im Diff |
| `CLAUDE.md` unveraendert | nicht im Diff |

## TDD Gate Compliance

Nicht anwendbar. Der Plan traegt `type: execute`, keine Aufgabe ist mit `tdd="true"` ausgezeichnet, und es ist keine Zeile Produktionscode entstanden: die acht Dateien sind ein Ablaufplan und sieben Messskripte. Das Gate aus Welle 1 laeuft trotzdem gegen jede von ihnen und war bei jedem der drei Task-Commits gruen, jeweils um fuenf Zusicherungen je neuer Datei gewachsen (86, 96, 106, 121).

---
*Phase: 10-vergleichsmessung-auf-der-aws-box*
*Completed: 2026-09-09*
