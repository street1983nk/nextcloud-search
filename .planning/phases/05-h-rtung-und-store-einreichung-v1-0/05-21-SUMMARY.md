---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 21
subsystem: infra
tags: [volllauf, arm64, ocr, speicher, drills, store-aussage, messbericht]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die Methode, den Grenzwert von 2,0 GB und die x86-Generalprobe aus Plan 05-14
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die drei Korrekturen aus Plan 05-20, im Abbild dieses Laufs
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die sechs Store-Texte aus Plan 05-17, die den gemessenen Satz tragen
provides:
  - Die Store-Aussage steht auf der Zielarchitektur, gemessen statt übertragen, 422,2 MB unter einer vom Kernel durchgesetzten Grenze von 2,0 GB
  - Ein vollständiger ARM-Volllauf über 50.000 Dateien und 20 GB mit null Fehlschlägen, samt Rohdaten im Repository
  - Die drei Korrekturen aus 05-20 sind im Feld abgelesen, jede an der Stelle, an der ihr Befund entstanden ist
  - Vier Störfall-Drills statt drei: der Neustart der ganzen Maschine ist der Produktivfall von DI-05-36 und jetzt gemessen
  - Die Frage nach INDEX_WORKERS ist beantwortet, und zwar mit einem Quelltextbefund statt mit einer Zahl
affects: [phase-review, 06-11-semantik-volllauf, store-einreichung-v1-0]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Behauptung über Stillstand wird an einer Handlung gemessen und nicht an einem Zustand: die Zahl der Poller-Durchgänge im Protokoll kann nicht zum falschen Zeitpunkt abgelesen werden, ein Zähler schon"
    - "Ein A/B mit identischem Byteinhalt braucht zwei Ordner und nicht zweimal denselben, weil der schnelle Weg von is_unchanged an der file_id hängt"
    - "Eine Wegwerf-Änderung am Abbild beweist ihre Enge mit zwei Baumhashen: einmal über alle Dateien, einmal ohne die geänderte, und die zweite Spalte muss gleich sein"
    - "Ein Zähler, den der Bericht nicht erwartet hat, wird erklärt und nicht weggelassen: sock_throttled steht neben den sechs OOM-Zählern mit dem Satz, was er nicht bedeutet"

key-files:
  created:
    - docs/measurements/2026-09-04-volllauf-m7g/README.md
    - docs/measurements/2026-09-04-volllauf-m7g/volllauf.csv
    - docs/measurements/2026-09-04-volllauf-m7g/statusseite.jsonl
    - docs/measurements/2026-09-04-volllauf-m7g/07-oom-beweis.txt
    - docs/measurements/2026-09-04-volllauf-m7g/22-drill1.txt
    - docs/measurements/2026-09-04-volllauf-m7g/25-neustart.txt
    - docs/measurements/2026-09-04-volllauf-m7g/23-drill2.txt
    - docs/measurements/2026-09-04-volllauf-m7g/24-drill3.txt
    - docs/measurements/2026-09-04-volllauf-m7g/31-workers-a.txt
    - docs/measurements/2026-09-04-volllauf-m7g/31-workers-b.txt
  modified:
    - docs/performance.md
    - README.md
    - docs/store-listing.md
    - backend/appinfo/info.xml
    - php/appinfo/info.xml
    - backend/tests/test_store_metadata.py
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Die Store-Zahl kommt aus dem ARM-Lauf und nicht aus der Generalprobe, auch wenn die ARM-Zahl kleiner ist: sie gilt für die Hardware, für die die Aussage gemacht wird, und der x86-Lauf bleibt als Vergleich daneben stehen"
  - "Der Neustart der Maschine wurde als vierter Drill gefahren, obwohl der Plan drei nennt: DI-05-36 hat ihn als den gefährlicheren der beiden Fälle vorhergesagt, und eine Vorhersage ohne Messung ist im Bericht nichts wert"
  - "Der eigene Messfehler in Drill 1b steht im Bericht statt korrigiert zu verschwinden, weil die Lehre daraus allgemein ist: ein Zustand, der zum falschen Zeitpunkt abgelesen wurde, sieht aus wie eine Bewegung"
  - "Keine Aussage dieses Berichts trägt eine Kernzahl der Generalprobe, weil das Repository sie zweimal verschieden nennt und die Maschine gelöscht ist (DI-05-39)"
  - "Die Zusatzmessung wird als Befund berichtet und nicht als Zahl: INDEX_WORKERS wird von keiner Stelle gelesen, also misst ein A/B mit 1 und 2 zweimal dasselbe Programm"
  - "Der Heilungszweig des Abgleichs wird ausdrücklich als nicht ausgelöst berichtet, statt die Zeile des Abgleichs als Beleg umzudeuten"

patterns-established:
  - "Eine Gegenrechnung Endung für Endung statt Kategorie für Kategorie: sie geht vollständig auf, braucht keine Sammelzeile und macht den Bestand der Instanz als eigene Spalte sichtbar"
  - "Wenn zwei Korrekturen ineinandergreifen, sagt der Bericht welche die andere seltener nötig macht, statt beide als gleichermaßen bewiesen zu führen"

requirements-completed: [SRCH-04]

# Metrics
duration: 2h10min (Fortsetzung), Volllauf 12h49min davor
completed: 2026-09-05
---

# Phase 5 Plan 21: Der ARM-Volllauf auf der Zielarchitektur Summary

**50.000 Dateien und 20 GB auf zwei ARM-Kernen mit 4 GB: 12 h 48 min, 50.021 indexiert, 28 mit benanntem Grund übersprungen, null fehlgeschlagen, höchster anon-Wert 422,2 MB gegen eine vom Kernel durchgesetzte Grenze von 2,0 GB, die kein einziges Mal berührt wurde.**

## Performance

- **Duration:** 2 h 10 min diese Fortsetzung (07:47Z bis 09:57Z), davor 12 h 49 min unbeaufsichtigter Volllauf
- **Started:** 2026-09-04T13:12:28Z (Box), 2026-09-04T17:46:36Z (erstes Verdikt), 2026-09-05T07:47Z (diese Fortsetzung)
- **Completed:** 2026-09-05T09:57Z
- **Tasks:** 3 des Plans, davon Task 1 und der Anstoß von Task 2 vor dieser Fortsetzung
- **Files modified:** 28, davon 21 neue Messdateien (ohne diesen SUMMARY)
- **Commits:** 8 auf `worktree-agent-05-21`

## Accomplishments

- **Die Store-Aussage steht auf der Hardware, für die sie gilt.** 422,2 MB (442.695.680 Byte) höchster `anon`-Wert, also 20,6 Prozent des Grenzwerts, gefahren unter `docker update --memory=2g --memory-swap=2g`. Alle sechs OOM-Zähler von `memory.events` und `memory.events.local` stehen auf null, auch `max` und `high`: die Grenze wurde in 46.127 Sekunden kein einziges Mal berührt. Die Zahl ist **kleiner** als die 428,6 MB der x86-Generalprobe, obwohl die Maschine schwächer ist, und das ist für eine Store-Aussage die richtige Richtung.
- **Die Verdikte gehen gegen den Generator auf, Endung für Endung, ohne Sammelzeile.** 20 erzeugte Übergrößen, 20 `too_large`, alle mit der Endung `.csv`, und die 768 erzeugten `.csv` minus 20 sind die 748 der Textspur. 9.916 einseitige plus 100 mehrseitige Scans ergeben exakt 10.016 PDF über die OCR-Spur, kein einziges der 22.536 Text-PDF ist mitgerutscht. Alle 100 Bilder gelesen. Die acht Ausnahmen sind sämtlich Nextcloud-Bestand: sieben Beispielfotos und ein Logo, zusammen mit 41 weiteren Bestandsdateien genau die 49, die die Crawl-Statistik für diesen Speicher führt.
- **Die drei Korrekturen aus 05-20 sind im Feld abgelesen.** Fünf Minuten Plattenpause mit zehn Rückgaben von je zwei Zeilen, und die höchste Auslieferungszahl steht unverändert auf eins: **null** abgeschriebene Zeilen, wo x86 an derselben Stelle 32 `failed(repeatedly_stuck)` erzeugt hat. Über elf Stunden OCR-Nachlauf **null** Aufnahmen mit `stalled`, höchster `stalledFor` 87 Sekunden, während der letzte Hintergrundauftrag 10 h 53 min alt war; x86 hatte hier acht Stunden Fehlanschuldigung.
- **Ein vierter Drill, den der Plan nicht kannte, und er ist der wichtigste.** DI-05-36 hatte den Neustart der Maschine als den gefährlicheren der beiden Fälle vorhergesagt. Gemessen: nach `systemctl reboot` kommt der Container nach seiner Regel `unless-stopped` von selbst hoch, beantwortet Suchen mit fünf Treffern, und macht in **10 Minuten 40 Sekunden keinen einzigen Poller-Durchgang** bei 130 wartenden Zeilen. Die harte Speichergrenze überlebt den Neustart, weil sie in der HostConfig steht.
- **Die Frage nach INDEX_WORKERS ist beantwortet, mit einem Quelltextbefund statt mit einer Zahl.** Zweihundert Scans zweimal, einmal mit 1 und einmal mit 2: 802 s gegen 799 s, und dieselbe Zeichenzahl auf das Zeichen. `grep` zeigt warum: die Konstante wird von keiner Stelle des Programms gelesen, die Serialität steckt in der Schleife `for job in claim.jobs` in `poller.py`. Als Nebenertrag eine Wiederholbarkeitszahl der OCR-Spur.
- **Die einzige Warnung aus dreizehn Stunden Arbeit ist vollständig aufgeklärt.** Eine verlorene Quittung über zwei Zeilen um 06:05:42Z, danach Sperrablauf, Wiederauslieferung, zweites Verdikt um 06:34:41Z mit `attempts = 3`. Kein Fehlschlag, kein Verlust, kein doppelter Eintrag: 50.021 ACL-Zeilen sind genau so viele wie die Dokumente im Index. Das ist die Zusage "mindestens einmal ausliefern, höchstens einmal indexieren", ungeplant und unter Last geprüft.

## Task Commits

1. **Rohdaten des Volllaufs und der vier Drills** - `573b727` (feat)
2. **Der Bericht trägt die ARM-Zahlen** - `4e29452` (docs)
3. **Die Store-Aussage auf der Zielhardware, dreisprachig, samt Gate** - `79c944f` (docs)
4. **DI-05-36 gemessen, DI-05-33 erledigt, DI-05-37 und DI-05-38 neu** - `d82fd02` (docs)
5. **Phasengrenze nachgerechnet, Kernzahl der Generalprobe offengelegt** - `c34228a` (fix)
6. **Die fünf Warnzeilen des Laufs einzeln benannt** - `8f98023` (docs)
7. **Die Entscheidung des Betreibers steht im Bericht** - `56cc8b3` (docs)

**Plan-Metadaten:** dieser SUMMARY (docs)

## Files Created/Modified

- `docs/measurements/2026-09-04-volllauf-m7g/`: 21 Dateien. `volllauf.csv` mit 9.622 Messpunkten im Abstand von fünf Sekunden, `statusseite.jsonl` mit 161 vollständigen Aufnahmen der Verwaltungsseite ohne Namensträger, der vierteilige OOM-Beweis vor jedem Eingriff erhoben, die vier Drill-Protokolle, der Bau des Wegwerf-Abbilds, beide Workers-Runden mit ihren Speicherreihen. Die `README.md` nennt Umgebung, beide Baumhashe, die Spalten der CSV, den Weg zum Nachbauen und erklärt die beiden Zahlen der Abschlusszeile, die eine Nachfrage provozieren.
- `docs/performance.md`: rund 800 geänderte Zeilen. Neu sind der Abschnitt "Der ARM-Volllauf", die vier ARM-Drills mit der abgelesenen Tabelle der drei Korrekturen, die Zusatzmessung und die Kostenrechnung des ARM-Laufs. Keine Zeile steht mehr auf FEHLT NOCH. Die x86-Abschnitte bleiben unangetastet daneben stehen.
- `README.md`, `docs/store-listing.md`, `backend/appinfo/info.xml`, `php/appinfo/info.xml`: der gemessene Satz nennt 422 MB auf ARM64 statt 429 MB auf x86, in allen drei Sprachen, und der Zusatz "die Wiederholung auf ARM steht aus" ist weg, weil sie gefahren ist.
- `backend/tests/test_store_metadata.py`: das mechanische Gate zitiert den neuen Satz. Es hält die Gleichheit über README und beide `info.xml`, und genau dafür ist es gebaut.
- `.planning/phases/05-*/deferred-items.md`: DI-05-33 erledigt, DI-05-36 um die Messung ergänzt, DI-05-37 bis DI-05-39 neu.
- Nicht angefasst, mit Absicht: `.planning/STATE.md`, `.planning/ROADMAP.md`, das Haupt-Repo und alle Dateien des parallel laufenden Plans 06-10.

## Decisions Made

- **Die kleinere Zahl geht in den Store, nicht die größere.** 422,2 MB auf ARM gegen 428,6 MB auf x86: die ARM-Zahl gilt für die Hardware, über die die Aussage gemacht wird, und sie ist auf der schwächeren Maschine nicht größer geworden. Beide Reihen stehen im Bericht nebeneinander, weil zwei Architekturen mehr über das Verhalten sagen als eine.
- **Der Neustart wurde gefahren, obwohl der Plan drei Drills nennt.** DI-05-36 hat ihn vorhergesagt, und eine Vorhersage ohne Messung trägt in einem Bericht nichts. Es hat sich gelohnt: der Fall ist eingetreten, und er hat nebenbei einen zweiten Befund erzeugt (DI-05-38).
- **Der eigene Messfehler bleibt im Bericht stehen.** Drill 1b hat zuerst das Gegenteil gemeldet, weil der Vergleichswert dreißig Sekunden vor dem Herunterfahren stammte und der Container in dieser Zeit noch zwei Dateien fertig gemacht hat. Die Korrektur steht als Nachtrag darunter, mit der Begründung, warum an Durchgängen und nicht an einem Zähler nachgemessen wurde.
- **Der Heilungszweig gilt als nicht ausgelöst und nicht als bewiesen.** Die Zeile des Abgleichs (`seen=50049 stale=20 missing=0 given_up=0`) wäre als Beleg umdeutbar gewesen. Sie belegt aber nur, dass nichts zu heilen war, und der Bericht sagt genau das, samt der Erklärung, warum: die erste Korrektur macht die zweite seltener nötig.
- **Keine Kernzahl der Generalprobe in irgendeiner Aussage.** Das Repository nennt sie an vier Stellen mit zwei und an einer mit drei, ein `nproc` von dieser Maschine ist nirgends aufgeschrieben, und die Maschine ist gelöscht. Der Vergleich nennt deshalb Architektur und Zeiten, nicht Kerne.
- **Das Wegwerf-Abbild beweist seine Enge mit zwei Baumhashen.** Über alle Python-Dateien unterscheiden sich die beiden Abbilder, ohne `config.py` sind sie identisch. Der Arbeitsbaum wurde nicht angefasst.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Ein vierter Drill: der Neustart der ganzen Maschine**

- **Found during:** Task 2, nach Drill 1
- **Issue:** Der Plan nennt drei Drills. DI-05-36 benennt zwei Fälle, in denen ein Container ohne AppAPI startet, und nennt den Neustart der Maschine ausdrücklich den gefährlicheren, weil ihn ein Kernel-Update von selbst auslöst. Drill 1 prüft nur den harmlosen Fall, den Handgriff eines Verwalters.
- **Fix:** Drill 1b gefahren: `systemctl reboot`, danach zehn Minuten Beobachtung ohne jeden Eingriff, gemessen an der Zahl der Poller-Durchgänge im Protokoll. Ergebnis null Durchgänge bei 130 wartenden Zeilen. Anschließend Heilung über AppAPI, drei Sekunden, erste neue Datei nach zehn Sekunden.
- **Files modified:** docs/measurements/2026-09-04-volllauf-m7g/25-neustart.txt, docs/performance.md, deferred-items.md
- **Verification:** `docker logs --since <Containerstart> | grep -c "pass finished"` gibt null über 10 min 40 s
- **Committed in:** `573b727`, `4e29452`, `d82fd02`

**2. [Rule 1 - Bug] Das erste Urteil von Drill 1b war falsch, und der Fehler war meiner**

- **Found during:** Task 2, Drill 1b
- **Issue:** Der Vergleichswert stammte aus einer Aufnahme rund dreißig Sekunden vor dem Herunterfahren. In dieser Zeit hat der Container noch zwei Dateien beurteilt, der Zähler stand danach also von selbst höher, und das Skript hat daraus "der Poller arbeitet wieder von selbst" geschlossen. Ein Zustand, der zum falschen Zeitpunkt abgelesen wurde, sieht aus wie eine Bewegung.
- **Fix:** Nachgemessen an der Zahl der Poller-Durchgänge im Protokoll, gezählt ab dem Start des Containers. Eine Handlung statt eines Zustands, und damit gegen diesen Fehler immun. Das falsche Urteil und seine Korrektur stehen beide in `25-neustart.txt` und im Bericht.
- **Files modified:** docs/measurements/2026-09-04-volllauf-m7g/25-neustart.txt, docs/performance.md
- **Verification:** null Durchgänge über fünf weitere Minuten, danach die Heilung mit sofortiger Bewegung
- **Committed in:** `573b727`, `4e29452`

**3. [Rule 1 - Bug] Die Phasengrenze der beiden Spuren war um acht Verdikte falsch**

- **Found during:** Task 5, beim Gegenlesen des Berichts
- **Issue:** Der erste Abschnitt war mit 40.516 Verdikten angegeben, gerechnet als Differenz aus Gesamtzahl und OCR-Dateien des zweiten Abschnitts. Richtig sind 40.524: im zweiten Abschnitt liegen neben den 9.505 OCR-Dateien noch 20 `too_large`, die der Abgleich um 06:31Z ein zweites Mal vorgelegt hat.
- **Fix:** Beide Zeilen der Tabelle aus der Zustandsdatenbank neu abgefragt, die Spaltenüberschrift von "Dateien" auf "Verdikte" gestellt und die 20 Wiedervorlagen mit ihrer Herkunft benannt.
- **Files modified:** docs/performance.md
- **Verification:** `select count(*) from files where indexed_at <= <Grenze>` gibt 40.524, `> <Grenze>` gibt 9.525
- **Committed in:** `c34228a`

**4. [Rule 2 - Missing Critical] Die Store-Texte trugen weiter die x86-Zahl und den Vorbehalt**

- **Found during:** Task 5
- **Issue:** Der Plan nennt in `files_modified` nur `docs/performance.md`, `README.md`, `docs/measurements/` und ein Ops-Skript. Der gemessene Satz steht aber außerdem in beiden `info.xml` und in `docs/store-listing.md`, jeweils dreisprachig, und `backend/tests/test_store_metadata.py` hält die Gleichheit über drei dieser Orte mechanisch. Ein aktualisiertes README ohne die anderen fünf Stellen hätte das Gate rot gemacht, und ein aktualisiertes Gate ohne die Store-Texte hätte die Store-Beschreibung mit einer überholten Zahl und dem Satz "die Wiederholung auf ARM steht aus" stehen lassen, obwohl sie gefahren ist.
- **Fix:** Alle sechs Texte nachgezogen, in Englisch, Deutsch und Französisch, mit dem Satz und seinem Zusatz. Der Zusatz sagt jetzt, dass auf der Zielhardware gemessen wurde und dass der Bericht beide Läufe trägt. `docs/store-listing.md` erklärt zusätzlich, warum die Zahl kleiner geworden ist, obwohl die Maschine schwächer ist.
- **Files modified:** README.md, docs/store-listing.md, backend/appinfo/info.xml, php/appinfo/info.xml, backend/tests/test_store_metadata.py
- **Verification:** `test_store_metadata.py` 14 Tests grün, beide `info.xml` wohlgeformt, keine Sprache fehlt, keine Länge überschritten, keine verbotenen Zeichen
- **Committed in:** `79c944f`

**5. [Rule 1 - Bug] Der Bericht sagte an drei Stellen, der Verbleib der Box sei offen**

- **Found during:** nach dem Owner-Entscheid vom 05.09.
- **Issue:** Abnahme und Entscheidung lagen vor, der Bericht sagte weiter "steht noch", "Zwischenstand" und "die Entscheidung trifft der Betreiber". Ein abgenommener Bericht, der über seinen eigenen Gegenstand etwas Überholtes sagt, wird beim nächsten Lesen zur Fehlerquelle.
- **Fix:** Stand-Tabelle, Kostenzeile und der Abschnitt zum Verbleib nachgezogen. Die Begründung mit ihren drei Wegen bleibt vollständig stehen, weil eine Entscheidung ohne ihre Alternativen nicht nachvollziehbar ist, und die Endkosten sind mit ihrer Unschärfe benannt statt geraten.
- **Files modified:** docs/performance.md
- **Verification:** kein "FEHLT NOCH" und keine Stelle mehr, die den Verbleib offen nennt
- **Committed in:** `56cc8b3`

---

**Total deviations:** 5 auto-fixed (2 Fehler, 3 fehlende Notwendigkeit)
**Impact on plan:** Ein zusätzlicher Drill und fünf zusätzliche Dateien gegenüber `files_modified`, alle fünf im Umkreis der Store-Aussage, die dieser Plan trägt. Kein neues Paket, keine Produktänderung, keine Datei des parallel laufenden Plans 06-10.

## Issues Encountered

- **Die Zusatzmessung konnte nicht messen, was sie messen sollte.** `INDEX_WORKERS` wird von keiner Stelle des Programms gelesen; die Konstante beschreibt die Serialität, statt sie zu setzen. Das A/B lief damit zweimal gegen dasselbe Programm, was die identische Zeichenzahl beider Runden auch zeigt. Der Bericht führt es als Befund, nennt die Frage des Betreibers beantwortet und sagt dazu, was ein echter zweiter Arbeiter kosten würde: eine nebenläufige Schleife in `poller.py` samt Schreibpuffer, Sperrfristen und zwei gleichzeitigen OCR-Spitzen von 300 bis 600 MB, die die Rechnung des Grenzwerts nicht verträgt. Notiert als DI-05-37.
- **Ein Neustart räumt `/tmp`, und darin lagen die Passwortdateien.** Das Auswerteskript von Drill 1b ist unmittelbar nach dem Neustart daran gestorben. Beide Passwörter neu gesetzt und unter `/home/ubuntu/work/.pw/` abgelegt, der Helfer liest jetzt von dort. Im Bericht steht es als Randnotiz bei Drill 1b.
- **Ein `pkill -f` auf einer ssh-Kommandozeile trifft die eigene Sitzung.** Das Muster steht in der Zeile, die es sucht. Die Box hat die Verbindung abgeworfen, ohne Schaden am Lauf. Genau davor warnt `starte-beobachter.sh` auf der Box seit dem ersten Anlauf, und die Warnung war zu lesen gewesen.
- **Die Python-Dateien im Abbild tragen CRLF**, weil der Arbeitsbaum von Windows kommt und als tar auf die Box gereicht wurde. Ein `sed`-Muster mit `$` findet dort nichts, weshalb der erste Bau des Wegwerf-Abbilds fehlschlug. Die Ersetzung läuft jetzt über Python auf Bytes. Steht im Bericht, weil es jeden trifft, der in diesem Abbild etwas sucht.
- **`ruff format --check` über das ganze Repository ist rot, und zwar seit vorher.** Acht Markdown-Dateien mit eingebetteten Python-Blöcken, davon sieben Planungsdokumente und `docs/performance.md`. Gegen den Stand vor diesem Plan gegengeprüft: `docs/performance.md` war bereits betroffen. CI ruft ruff mit `working-directory: backend` auf, prüft also nur den Container-Teil, und der ist sauber. Nicht angefasst, weil außerhalb dieses Plans.

## User Setup Required

Keine. Der Betreiber hat am 05.09. abgenommen und die Box anhalten lassen; `stop-instances` hat der Orchestrator abgesetzt.

## Next Phase Readiness

- **Die Store-Einreichung kann auf diesen Bericht zeigen.** Alle sechs Store-Texte tragen die gemessene Zahl der Zielarchitektur, das mechanische Gate hält die drei Orte gleich, und `docs/performance.md` trägt Methode, Kurve, Korpus, OOM-Beweis, vier Drills und beide Läufe nebeneinander.
- **Phase 6 findet ihre Maschine wieder.** Die Box ist angehalten und nicht abgebaut, also bleiben Korpus (20,12 GB, 43 min Erzeugung), Index (761 MB, 12 h 49 min Rechenzeit) und beide Abbilder erhalten. Beim nächsten Start ist zweierlei nachzuziehen: `BOX_IP` in `C:\Users\Student\.findling-loadtest\box.env` und der DNS-Eintrag `loadtest.infranode.dev`, denn eine angehaltene Instanz gibt ihre öffentliche Adresse zurück. Beides steht in der Zustandsdatei.
- **Vier Punkte für den Phase-Review, einer mit Vorrang:**
  - **DI-05-36 (Vorrang):** ein Containerstart ohne AppAPI hinterlässt einen Container, der Suchen beantwortet und nie wieder indexiert. Jetzt für beide Fälle gemessen, auch für den Neustart der Maschine. Die Abhilfe ist eine Entscheidung darüber, woher ein frisch gestarteter Container weiß, ob er eingeschaltet ist, mit mehreren Kandidaten und verschiedenen Nachteilen.
  - **DI-05-38:** die Verwaltungsseite kann genau diesen Zustand nicht anzeigen. `stalledFor` nimmt die spätere von zwei Bewegungen, damit ein langer OCR-Nachlauf nicht als Stillstand gilt, und kann deshalb nicht zwischen "beide Hälften stehen" und "nur die Container-Hälfte steht" unterscheiden. Gehört hinter DI-05-36: wer den einen behebt, macht den anderen fast gegenstandslos.
  - **DI-05-37:** `INDEX_WORKERS` steuert nichts. Vorschlag ohne Verhaltensänderung: ein Satz im Docstring, der sagt, wo die Serialität wirklich herkommt.
  - **DI-05-39:** die Kernzahl der Generalprobe steht an fünf Stellen, an vier mit zwei und an einer mit drei. Zu klären mit dem Katalog des Anbieters, vor einer Store-Einreichung, die den Bericht verlinkt.
- **Was der Orchestrator übernimmt:** Merge nach `main`, `.planning/STATE.md`, `.planning/ROADMAP.md` und die Fortschreibung von DI-05-33 und DI-05-34 in der Konsolidierung.

## Self-Check: PASSED

| Prüfung | Ergebnis |
|---|---|
| `docs/measurements/2026-09-04-volllauf-m7g/` | vorhanden, 21 Dateien plus README |
| `volllauf.csv`, `statusseite.jsonl`, `07-oom-beweis.txt` | vorhanden, 9.622 Messzeilen, 161 Aufnahmen, vier Teile |
| `22-drill1.txt`, `25-neustart.txt`, `23-drill2.txt`, `24-drill3.txt` | alle vier vorhanden |
| `31-workers-a.txt`, `31-workers-b.txt` mit ihren CSV | vorhanden, je 200 Dateien, 802 s und 799 s |
| `docs/performance.md` | kein "FEHLT NOCH" mehr, keine Stelle nennt den Verbleib der Box offen |
| Commits `573b727`, `4e29452`, `79c944f`, `d82fd02`, `c34228a`, `8f98023`, `56cc8b3` | alle im Log |
| `uv run pytest` im Backend | 992 bestanden, 11 übersprungen |
| `ruff check`, `ruff format --check`, `pyright`, `vulture` im Backend | alle sauber |
| `test_store_metadata.py` gegen den neuen Satz | 14 Tests grün |
| Em-Dash, En-Dash, Emoji in allen geänderten Dateien | keine |
| Zeilenenden im Index | LF, `core.autocrlf` erledigt den Arbeitsbaum |
| Branch, Namensraum, Arbeitsverzeichnis vor jedem Commit | `worktree-agent-05-21`, geprüft |
| `.planning/STATE.md`, `.planning/ROADMAP.md`, Haupt-Repo | nicht angefasst |
| Dateien des parallel laufenden Plans 06-10 | nicht angefasst |

Was diese Selbstprüfung **nicht** mehr leisten kann: eine Gegenprobe auf der Box. Sie ist seit dem 05.09. angehalten, und jede Zahl dieses SUMMARY steht deshalb entweder im Repository oder in den Rohdaten unter `docs/measurements/2026-09-04-volllauf-m7g/`. Genau dafür liegen sie dort.

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-05*
