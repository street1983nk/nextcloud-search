---
phase: 05-h-rtung-und-store-einreichung-v1-0
plan: 14
subsystem: infra
tags: [load-testing, cgroup-v2, oom, ocr, tesseract, nextcloud-aio, harp, postgres, resilience, hetzner]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: die laufende Box mit AIO über HaRP, die gemessene Grundlast und den Messbericht aus Plan 05-10
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: den Grenzwert von 2,0 GB, den Härtungsbefehl, den OCR-Faktor, die Prognose und das Abbild mit dem xlsx-Fix aus Plan 05-12
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: Korpusgenerator, RSS-Sampler und Box-Werkzeug aus Plan 05-05
provides:
  - Erfolgskriterium 1 der Phase auf x86 belegt, ARM steht aus: 50.104 Dateien, jede mit Verdikt, null Fehlschläge, Spitze 428,6 MB anon unter einer harten 2-GB-Grenze, kein Speichertod
  - Die Store-Zahl als gemessene Größe mit ihrer Kurve, ihrer Methode und ihren Grenzen, verlinkt aus dem README
  - D-05 erfüllt: die drei Störfälle sind auf echter Hardware durchgespielt, jeder mit benannter Grenze
  - D-06 erfüllt: der volle Bericht in docs/performance.md, die verdichtete Kernaussage im README
  - D-01 erfüllt: Box, Volume und Firewall gelöscht und gegen die API geprüft, Kosten 0,82 EUR
  - Drei Befunde des Dauerbetriebs, die kein CI-Auftrag finden konnte: DI-05-22, DI-05-23 und die berichtigte Ursache für "Container läuft, indexiert nicht"
affects: [05-17-store-beschreibung, arm-volllauf-cax11, fix-plan-di-05-22-23, phase-review]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Den gemessenen Codestand über einen Baumhash der Quelldateien belegen statt über den Namen eines Kennzeichens: ein Kennzeichen kann jeder vergeben, ein Hash ist aus dem Arbeitsbaum nachrechenbar, auch wenn die Messmaschine längst gelöscht ist"
    - "Vor einer Messung, die einen Tag dauert, den Zustand nicht säubern, sondern neu herstellen: Datenspeicher löschen statt Tabellen korrigieren"
    - "Eine unbeaufsichtigte Messung schreibt zwei Reihen mit, eine feine für den Gegenstand und eine grobe für den Zusammenhang, beide mit Zeitstempel und ohne Lücke"
    - "Eine Prognose aus dem Anfang eines kurzen Laufs überschätzt den Dauerbetrieb, weil der Anlauf sich auf nichts verteilt"
    - "Ein Störfall-Drill braucht einen eigenen, kurzen Vorrat, wenn der Lauf schon fertig ist, und er braucht ihn auf dem Weg, den ein Mensch nimmt"
    - "Eine Zuordnung, die zeitlich naheliegt, ist keine Ursache: erst die zweite Beobachtung mit anderem Verhältnis trennt die beiden"

key-files:
  created:
    - docs/measurements/2026-09-04-volllauf-cpx22/README.md
    - docs/measurements/2026-09-04-volllauf-cpx22/volllauf.csv
    - docs/measurements/2026-09-04-volllauf-cpx22/statusseite.csv
    - docs/measurements/2026-09-04-volllauf-cpx22/07-oom-beweis.txt
    - docs/measurements/2026-09-04-volllauf-cpx22/08-drill1.txt
    - docs/measurements/2026-09-04-volllauf-cpx22/10-drill3.txt
    - docs/measurements/2026-09-04-volllauf-cpx22/11-drill2.txt
    - docs/measurements/2026-09-04-volllauf-cpx22/01-korpus.log
    - docs/measurements/2026-09-04-volllauf-cpx22/06-start.log
  modified:
    - docs/performance.md
    - README.md
    - .planning/phases/05-h-rtung-und-store-einreichung-v1-0/deferred-items.md

key-decisions:
  - "Das Abbild wurde nicht neu gebaut, sondern nachgerechnet: der Baumhash über die 44 Python-Dateien ist im Arbeitsbaum und im laufenden Abbild derselbe, und zwischen dem Stand des Abbilds und dem Arbeitsbaum liegt keine Änderung unter backend/, php/ oder docker/"
  - "Der Volllauf startet auf einem leeren Index über app_api:app:unregister --rm-data, weil die Store-Aussage über eine frische Installation getroffen wird und ein halb gefüllter Index etwas anderes misst"
  - "Die Zustandstabellen wurden vor dem Lauf geräumt (DI-05-21), damit der Fehlerbericht des Volllaufs keine Zeilen über Dateien trägt, die es nicht mehr gibt"
  - "Die Störfall-Drills laufen gegen einen eigenen kurzen Vorrat aus 300 beziehungsweise 60 Scans, über WebDAV hochgeladen, statt den Volllauf zu wiederholen: der Eingriff fällt damit sicher in die OCR-Arbeit, und ein Verlust kostet Minuten statt zehn Stunden"
  - "Die Verknappung der Platte lässt bewusst 400 MB frei statt null, damit die PostgreSQL-Datenbank derselben Instanz nicht in Mitleidenschaft gezogen wird: eine Probe, die die Messmaschine beschädigt, misst am Ende etwas anderes"
  - "Die CAX11-Zeilen des Berichts bleiben auf FEHLT NOCH, gegen das Abnahmekriterium des Plans und nach dem Owner-Entscheid 'beides': dieser Lauf ist die x86-Generalprobe, der ARM-Volllauf folgt separat"
  - "Die Statuszeile des README wurde berichtigt, weil sie 'There is no indexing and no real search in this phase' behauptete und damit unmittelbar über einer Messung von 50.000 indexierten Dateien stand"

patterns-established:
  - "Der vierteilige OOM-Beweis, vollständig zitiert statt zusammengefasst: memory.events, docker inspect, der Spitzenwert aus der CSV und memory.peak mit dem Cache-Anteil"
  - "Jede Aussage eines Drills nennt ausdrücklich, was sie nicht beweist, und diese Sätze stehen im Bericht und nicht in einer Fußnote"
  - "Wenn eine Zuordnung sich als falsch erweist, wird sie im Bericht berichtigt und nicht stillschweigend ersetzt: der entlastete Verdächtige steht mit dem Grund seiner Entlastung da"

requirements-completed: [PKG-03]

# Metrics
duration: 15h 40m (davon 10h 14m unbeaufsichtigter Volllauf)
completed: 2026-09-04
---

# Phase 5 Plan 14: Der Volllauf, die Störfälle und der Abbau Summary

**Ein Index- und OCR-Lauf über 50.104 Dateien und 20,2 GB ist auf einer 4-GB-Box in 10 h 14 min durchgelaufen, ohne einen einzigen Fehlschlag und ohne dass der Kernel die 2-GB-Grenze auch nur einmal berührt hätte; die Spitze liegt bei 428,6 MB, also bei einem Fünftel des Grenzwerts, die drei Störfälle sind auf derselben Hardware durchgespielt, und die Box ist gelöscht und gegengeprüft, für 0,82 EUR.**

## Performance

- **Duration:** 15h 40m Wanduhr, davon 10h 14m unbeaufsichtigter Lauf und 28 min Korpuserzeugung
- **Started:** 2026-09-03T19:40:00Z
- **Completed:** 2026-09-04T11:30:00Z
- **Tasks:** 3, davon einer als blockierender Checkpoint mit Abnahme durch den Owner
- **Files modified:** 12 Dateien, davon 9 neu

## Accomplishments

- **Erfolgskriterium 1 der Phase ist auf x86 belegt, und zwar strenger als verlangt.** Der Plan fordert einen Lauf ohne Speichertod unter einem Grenzwert. Gemessen ist mehr: `memory.events` zeigt nicht nur `oom_kill 0`, sondern auch `max 0` und `high 0`. Der Kernel hat die Grenze in 36.854 Sekunden **kein einziges Mal** berührt, es gab also nicht einmal einen Beinahe-Fall. Der Spitzenwert von `anon` liegt bei 449.441.792 Byte, das sind 20,9 Prozent des Grenzwerts von 2,0 GB.
- **Jede Datei hat ein Verdikt, und die Zählung geht gegen die Erzeugung auf.** 50.068 indexiert, 36 übersprungen, **null fehlgeschlagen**. Die 20 absichtlich zu grossen Dateien erscheinen als genau 20 `too_large`. Die OCR-Zahl stimmt bis auf 18 Dateien, und die 18 sind die Beispielfotos, die Nextcloud jedem neuen Nutzer mitgibt. Der xlsx-Befund aus 05-12 ist auf hundertfacher Menge erledigt: alle 3.345 Tabellen indexiert, die Gruppe `corrupt` kommt in keiner der 130 Aufnahmen vor.
- **Der Lauf endete nicht dort, wo es aussah.** Um 01:30Z war der Crawl fertig, und eine Ablesung zu diesem Zeitpunkt hätte 2,3 Stunden Laufzeit ergeben und die Prognose blamiert. Das letzte Verdikt fiel um 09:27Z: der OCR-Nachlauf lief acht Stunden allein weiter. Die richtige Zahl ist 10 h 14 min, und sie liegt 22 Prozent unter der Prognose.
- **Die Prognose ist nicht nur verglichen, sondern erklärt.** Der OCR-Posten lag mit 2,80 s je Seite gegen gemessene 3,16 s je Datei knapp richtig. Danebengelegen hat die Textspur, um den Faktor zwei, und der Grund ist benennbar: die 0,43 s je Datei stammten aus den ersten 170 Sekunden des Trockenlaufs, also aus einem Anlauf, der sich über 40.000 Dateien auf nichts verteilt.
- **Die Kurve sagt drei Dinge, die eine einzelne Zahl nicht sagen kann.** Die Spitze fällt in die erste halbe Stunde und wird in den folgenden zehn Stunden nie wieder erreicht; der Median bleibt über den ganzen Lauf zwischen 240 und 364 MB, obwohl der Index von null auf 726 MB wächst, es gibt also kein Leck; und `memory.peak` steht ab der zweiten Stunde still, obwohl er den Dateicache mitzählt.
- **Die drei Störfälle sind durchgespielt, und zwei davon haben etwas gefunden.** Der Abschuss mitten im OCR-Lauf hat der Anwendung nichts gekostet: 298 von 300 Dateien fortgesetzt, keine Doppelung, Wiederaufnahme in 11 Sekunden, und die beiden gesperrten OCR-Aufträge erledigten sich nach dem Ablauf ihrer Sperre von selbst. Die Platten-Probe dagegen hat einen Befund geliefert, der die Zusage ihres eigenen Banners einschränkt, und die Backend-Probe hat eine Zuschreibung aus 05-12 berichtigt.
- **Die Box ist weg, und das ist geprüft und nicht behauptet.** Server, Volume und Firewall sind gegen die API auf `not_found` geprüft, und eine unabhängige Abfrage über fünf Ressourcenarten nach dem Kennzeichen `purpose=findling-phase5` liefert null Treffer. Gesamtkosten 0,82 EUR brutto bei 19,2 Stunden.

## Task Commits

1. **Task 1a: Vorbereitung und Start des Volllaufs** - `2c64bf2` (docs)
2. **Task 1b und Task 2: Volllauf gemessen, drei Störfälle durchgespielt** - `13d3713` (feat)
3. **Task 3, Vorarbeit: Kernaussage im README, zwei Befunde notiert** - `33ad40f` (docs)
4. **Nachtrag zu Drill 3 und eine berichtigte Zuordnung** - `75201c4` (fix)
5. **Task 3: Abbau der Box und Kosten** - `d34d479` (docs)

**Plan-Metadaten:** dieser SUMMARY (docs)

## Files Created/Modified

- `docs/performance.md`: wächst von 1213 auf 2028 Zeilen. Neu sind "Die Vorbereitung des Volllaufs" (Nachweis des Codestands über den Baumhash, die drei Räumungen, der Korpus mit Gegenprobe an den Dateiendungen, die harte Grenze), "Findling im Volllauf" mit sieben Unterabschnitten (Zahlen, vierteiliger OOM-Beweis, Kurve je Stunde, Prognosevergleich, Indexgröße, die Statusseite über den ganzen Lauf), "Die Störfall-Drills" mit drei Drills und einem Nachtrag, sowie "Was der Test gekostet hat" samt Abbau und Gegenprobe.
- `docs/measurements/2026-09-04-volllauf-cpx22/`: 7.782 Messpunkte des Samplers, 130 Aufnahmen der Statusseite auf 21 Felder verdichtet, der OOM-Beweis, drei Drill-Protokolle, das Korpusprotokoll und der Startlauf, dazu ein README mit Umgebung, Spaltenbedeutung und Nachbauanleitung. Zusammen 624 KB.
- `README.md`: neuer Abschnitt "What it costs in memory, measured" mit der Kernaussage in der Form aus D-06 und dem Verweis auf den Bericht; dazu die berichtigte Statuszeile, siehe Deviations.
- `deferred-items.md`: DI-05-22 und DI-05-23, dazu ein Erledigungsvermerk an DI-05-21.

## Decisions Made

- **Nachgerechnet statt neu gebaut.** Der Volllauf durfte nicht gegen ein Abbild ohne den xlsx-Fix laufen, und der Name eines Kennzeichens ist dafür kein Beleg. Verglichen wurde deshalb der Inhalt: ein Hash über jede Python-Datei des Pakets, auf Zeilenenden vereinheitlicht, weil der Arbeitsbaum auf Windows liegt und das Abbild auf Linux gebaut ist. Arbeitsbaum und Abbild liefern dieselbe Zahl, und zwischen beiden Ständen liegt keine Änderung unter `backend/`, `php/` oder `docker/`. Der Hash ist zugleich das, was den Abbau überlebt: das Abbild wurde auf der Messmaschine gebaut und existiert nirgends sonst, der Hash ist jederzeit nachrechenbar.
- **Leerer Index statt geräumter Tabellen.** Die Store-Aussage handelt von einer frischen Installation, also musste der Lauf von null beginnen. `--rm-data` ist der einschneidende, aber richtige Weg; nebenbei belegt er D-16 in seiner zweiten Richtung, nachdem 05-12 die erste belegt hatte.
- **Eigener kurzer Vorrat für die Drills.** Der Volllauf war fertig, als die Drills anstanden. Ihn zu wiederholen hätte zehn Stunden gekostet und einen Verlust teuer gemacht. 300 Scans, über WebDAV hochgeladen, geben ein Fenster von 20 Minuten, in dem der Eingriff sicher in die OCR-Arbeit fällt.
- **400 MB Rest statt null.** Der Schwellwert der Anwendung liegt bei 500 MB, die Datenbank derselben Instanz liegt auf demselben Dateisystem. Die Verknappung unterschreitet den Schwellwert sicher und lässt der Datenbank Luft. Eine Probe, die die Messmaschine beschädigt, misst am Ende etwas anderes als sie sollte.
- **Die CAX11-Zeilen bleiben FEHLT NOCH.** Das Abnahmekriterium des Plans verlangt einen Bericht ohne als fehlend markierte Abschnitte. Der Owner-Entscheid "beides" verlangt die Zwei-Läufe-Struktur. Der Entscheid schlägt das Kriterium, und der Bericht benennt die Lücke ausdrücklich, statt sie zu verschweigen.
- **Suche während der Plattenpause nachgemessen.** Der erste Durchgang von Drill 3 liess die Zusage des Banners "Search keeps working" ungeprüft. Der Owner hat den Nachtrag freigegeben, und er hat sich doppelt bezahlt gemacht: die Zusage stimmt, und derselbe Durchgang hat den schwersten Befund dieses Plans geliefert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die Statuszeile des README behauptete das Gegenteil der Messung**

- **Found during:** Task 3, beim Einsetzen der Kernaussage
- **Issue:** Die zweite Zeile des README lautete "Status: Phase 1, walking skeleton, not usable yet. There is no indexing and no real search in this phase." Der neue Abschnitt darunter berichtet von 50.000 indexierten Dateien. Ein öffentliches Artefakt, das sich auf zwei Bildschirmzeilen selbst widerspricht, ist kein Formfehler, sondern eine falsche Aussage über den Zustand des Produkts.
- **Fix:** "Status: hardening before the first store release, not submitted yet", mit dem Hinweis, dass die Freigabeartefakte vorbereitet werden und bis zur Veröffentlichung im Store nicht auf einem Produktionsserver installiert werden soll.
- **Files modified:** README.md
- **Verification:** vom Owner ausdrücklich abgenommen ("der neue Text passt")
- **Committed in:** `33ad40f`

**2. [Rule 3 - Blocking] `occ app_api:app:register --info-xml` liest den Pfad im Container, nicht auf dem Wirt**

- **Found during:** Task 1, beim Neuaufsetzen der ExApp vor dem Lauf
- **Issue:** Das Skript reichte einen Wirtspfad an `--info-xml` weiter. `occ` läuft im Nextcloud-Container, findet die Datei nicht und bricht mit "Failed to read info.xml" ab, und zwar **nachdem** die alte Registrierung bereits entfernt war. Der Volllauf war damit blockiert.
- **Fix:** `docker cp` der Datei in den Nextcloud-Container, danach den Pfad dort verwenden. Im Skript auf der Box korrigiert und im Bericht als Fussangel notiert, weil sie eine Viertelstunde gekostet hat.
- **Files modified:** keine im Repository, die Korrektur betrifft ein Werkzeug auf der Messmaschine; der Hinweis steht in `docs/performance.md`
- **Verification:** die Registrierung lief danach beim ersten Versuch durch
- **Committed in:** `2c64bf2` (als Absatz im Bericht)

**3. [Rule 1 - Bug] Eine Zuordnung im eigenen Bericht war falsch**

- **Found during:** Task 3, im Nachtrag zu Drill 3
- **Issue:** Der Bericht schrieb zwei gestrandete Dateien dem `docker kill` zu, weil er zeitlich davorlag. Der Nachtrag hat 30 gleichartige Abschreibungen ohne jeden Abschuss erzeugt, und ihre Zahl war beide Male exakt die Zahl der Zeilen, die bei Beginn der Plattenpause unterwegs waren. Die Ursache ist die Plattenknappheit, nicht der Abschuss.
- **Fix:** Drill 1 entlastet und die Bilanz dort auf "der Abschuss hat keine einzige Datei gekostet" berichtigt, der Hergang samt Mechanismus zu Drill 3 verschoben, DI-05-23 neu gefasst. Der entlastete Verdacht steht mit dem Grund seiner Entlastung im Bericht, statt stillschweigend zu verschwinden.
- **Files modified:** docs/performance.md, deferred-items.md
- **Committed in:** `75201c4`

### Nicht behoben, sondern notiert

**4. [Rule 4 - Architectural] Eine halbe Minute Plattenknappheit schreibt den ganzen Vorrat ab (DI-05-23)**

Der schwerste Befund dieses Plans, und er wäre in CI nicht zu finden gewesen. `QueueMapper` zählt die Wiederholung **bei der Ausgabe** hoch, der Container gibt bei knapper Platte die ganze Ladung unbeurteilt zurück, ein Durchgang des Pollers dauert wenige Sekunden, und `MAX_DELIVERIES` steht auf 3. Nach rund zwanzig Sekunden Knappheit ist das Budget jeder unterwegs befindlichen Zeile aufgebraucht, und sie wird als `failed(repeatedly_stuck)` abgeschrieben. Zweimal reproduziert, mit 2 von 2 und mit 30 von 30 Zeilen. Die Oberfläche sagt in derselben Minute "Indexing is paused so the index stays intact", und das ist für den Index wahr und für den Arbeitsvorrat falsch. Die Dateien sind nicht unbemerkt weg, aber der nächtliche Vergleich holt sie ausdrücklich nicht zurück.

**5. [Rule 4 - Architectural] Die Statusseite sagt acht Stunden lang "kommt nicht voran" (DI-05-22)**

`runState` liest `stalled`, wenn Arbeit wartet und der letzte Hintergrundauftrag dieser App länger als eine halbe Stunde zurückliegt. Der Crawl endete um 01:30Z, der Container arbeitete bis 09:27Z weiter und quittiert über OCS. Über die Mehrheit der Laufzeit stand die falsche Anschuldigung auf der Seite, während der Deckungsgrad in derselben Reihe von 82 auf 99 Prozent stieg. Auf einer gewöhnlichen Instanz fällt das nicht auf; auf der Zielhardware ist der OCR-Nachlauf 77 Prozent des Laufs.

**Beschlossene Nacharbeit:** Beide Befunde bleiben nicht liegen. Der Orchestrator zieht nach dem Merge dieses Plans einen kleinen Fix-Plan in die Phase, vor 05-17 und vor dem ARM-Volllauf, damit der ARM-Lauf das korrigierte Verhalten prüft.

---

**Total deviations:** 3 auto-fixed (2 Bugs, 1 blockierend), 2 als Befund notiert (beide Rule 4)
**Impact on plan:** Kein zusätzlicher Umfang, kein neues Paket, keine Änderung an Code des Produkts. Die beiden Rule-4-Befunde sind der eigentliche Zusatzertrag: sie beschreiben Verhalten, das nur ein zehnstündiger Lauf auf knapper Hardware zeigt.

## Issues Encountered

- **Eine Ablesung zum falschen Zeitpunkt hätte die Prognose blamiert.** Um 01:30Z war der Crawl fertig, die Warteschlange sah leer aus, und der Lauf schien nach 2,3 Stunden durch. Tatsächlich lief die OCR-Spur noch acht Stunden. Die Unterscheidung hängt an `MAX(indexed_at)` in der Zustandsdatenbank des Containers und nicht an dem, was die Warteschlange zeigt.
- **`docker start` stellt die Suche wieder her und die Indexierung nicht.** Der Container bedient danach `/status`, `/search` und `/snippets` mit 200, aber der Poller läuft nicht an. Die Ursache ist nicht der fehlende HaRP-Schlüssel, wie 05-12 vermutete: `findling.main.enabled_handler` bewaffnet Poller und Vergleichslauf, und AppAPI ruft ihn über `PUT /enabled` nur bei der Registrierung. Eigens nachgeprüft, weil der Befund dem Kill-Drill widerspricht, wenn man Lese- und Schreibweg nicht trennt.
- **Der Firewall-Abbau braucht zwei Aufrufe.** Die Bindung an den Server löst sich erst, nachdem der Server wirklich weg ist. Der erste `destroy` meldet `resource_in_use` und sagt ausdrücklich, dass etwas übrig ist; der zweite räumt sie ab. Das Skript behandelt jede unlesbare Antwort als "steht noch da", was hier genau richtig ist.
- **`pkill -f observe.py` über SSH tötet die eigene Sitzung**, weil die Befehlszeile der Sitzung das Muster enthält. Exitcode 255 und ein Prozess, der weiterläuft. Über die PID beendet.
- **Der Korpusgenerator schreibt sein Manifest dorthin, wohin man zeigt, auch wenn das im Container liegt.** `--report /out/../manifest.csv` landet im Dateisystem des Wegwerf-Containers und ist mit ihm weg. Kein Schaden: Seed, Dateizahl, Bytezahl und Listen-Prüfsumme stehen auf der Standardausgabe, und die Verteilung wurde von der Platte gegengeprüft.

## User Setup Required

Keine. Eine Aufgabe bleibt beim Orchestrator und ist dort angekündigt: der DNS-A-Eintrag `loadtest.infranode.dev` zeigt auf eine Adresse, die es nicht mehr gibt, und wird gesondert entfernt. `HCLOUD_TOKEN` in `C:\Users\Student\.findling-hcloud.env` wird für diese Phase nicht mehr gebraucht, bis der ARM-Volllauf ansteht.

## Next Phase Readiness

**Der Satz für Plan 05-17, zum Zitieren, in der Form aus D-06:**

> A full index and OCR run over 50,000 files and 20 GB on a 4-GB box peaked at 429 MB of resident anonymous memory, under a hard 2 GB limit enforced by the kernel, with no OOM kill.

Dazu gehört, in jeder der drei Sprachen, der Zusatz: die Maschine war x86, die Wiederholung auf ARM steht aus, und der Bericht nennt jede Zahl, die sie ersetzen wird.

**Was aus diesem Plan in den ARM-Volllauf geht:**

| Angabe | Wert | Gilt für ARM |
|---|---|---|
| Grenzwert | 2,0 GB für `anon` | unverändert |
| Härtungsbefehl | `docker update --memory=2g --memory-swap=2g` | unverändert |
| Korpus | Seed `phase5-full`, 50.000 Dateien, 20,2 GB | Prüfsumme nur bei gleichem Abbild |
| Spitzenwert | 428,6 MB | zu wiederholen |
| Laufzeit | 10 h 14 min | zu wiederholen, Spanne 18 bis 26 h bei doppeltem bis dreifachem OCR-Faktor |
| Indexgröße | 761.374.910 Byte | erwartbar gleich, der Index kennt keine Architektur |
| die drei Drills | durchgespielt | nicht zu wiederholen, sie hängen am Verhalten und nicht an der Architektur |

**Vor dem ARM-Volllauf zu erledigen:** der angekündigte Fix-Plan zu DI-05-22 und DI-05-23. Der zweite ist der wichtigere: solange eine kurze Plattenknappheit den Arbeitsvorrat abschreibt, ist ein Volllauf auf einer 4-GB-Box mit knappem Datenträger eine Wette. Der ARM-Lauf sollte das korrigierte Verhalten prüfen, dann ist die Behebung gleich mitbelegt.

**Offen aus dieser Phase, ausdrücklich nicht hier erledigt:** DI-05-19 verlangt Querverweise von `docs/admin-page.md` und `docs/ocr.md` auf `docs/performance.md`. Der Bericht trägt jetzt Zahlen, der Verweis lohnt sich also. Beide Dateien stehen nicht in den `files_modified` dieses Plans.

## Self-Check: PASSED

| Prüfung | Ergebnis |
|---|---|
| `docs/performance.md` | vorhanden, 2028 Zeilen (vorher 1213) |
| `README.md` | Kernaussage vorhanden, enthält `4-GB` und den Verweis auf `performance.md` |
| `docs/measurements/2026-09-04-volllauf-cpx22/` | 9 Dateien, 624 KB |
| Commits `2c64bf2`, `13d3713`, `33ad40f`, `75201c4`, `d34d479` | alle im Log |
| Gate Task 1 (`oom_kill`, `OOMKilled`, `memory.peak`, `50.000`, kein "archiv", keine Gedankenstriche) | grün |
| Gate Task 2 (`docker kill`, `paused_low_disk`, "Grenze" mindestens dreimal) | grün, 26 Vorkommen |
| Emojis in `docs/performance.md` und `README.md` | keine |
| Em-Dash und En-Dash in beiden | keine |
| `FEHLT NOCH` in `docs/performance.md` | 13, sämtlich CAX11-Zeilen, nach Owner-Entscheid so gewollt |
| Server, Volume, Firewall | gegen die API auf `not_found` geprüft |
| Label `purpose=findling-phase5` über fünf Ressourcenarten | null Treffer |
| `ssh root@62.238.114.125` | `Connection timed out` |
| Zustandsdatei des Box-Werkzeugs | entfernt |
| Code des Produkts angefasst | nein, weder `backend/` noch `php/` |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | nicht angefasst |
| Hintergrundläufe | Sampler und Beobachter geordnet beendet, Abschlusszeile geschrieben |

---
*Phase: 05-h-rtung-und-store-einreichung-v1-0*
*Completed: 2026-09-04*
