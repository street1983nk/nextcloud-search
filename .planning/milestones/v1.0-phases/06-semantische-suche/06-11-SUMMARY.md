---
phase: 06-semantische-suche
plan: 11
subsystem: measurement
tags: [arm-volllauf, semantik, kriterium-4, kriterium-5, d-17, idx-08, aws, memory-events, byte-je-dokument]

# Dependency graph
requires:
  - phase: 05-h-rtung-und-store-einreichung-v1-0
    provides: "05-21: die ARM-Box, der Korpus aus 50.000 Dateien, der Betriebsweg (AIO ueber HaRP, harte Grenze per docker update), der Volltextlauf als Vergleichszeile"
  - phase: 06-semantische-suche
    provides: "06-03: die dreimal gemessene sha256 der int8-Modelldatei, gegen die das Abbild dieses Laufs geprueft wurde"
  - phase: 06-semantische-suche
    provides: "06-04: die gerechnete Kennzahl 876,0 Byte je Dokument, die dieser Lauf durch die gemessene ersetzt"
  - phase: 06-semantische-suche
    provides: "06-07 und 06-09: die nachlaufende embed-Spur derselben Warteschlange und die zwei Deckungszahlen der Verwaltungsseite, aus denen der Statusbeobachter liest"
provides:
  - "docs/measurements/2026-09-05-semantiklauf-m7g/: der vollstaendige Messbericht mit Rohdaten (CSV mit 13.983 Aufnahmen, Statusreihe, OOM-Beweis, zwei Suchlastproben, Vektorbestand) und 15 Skripten"
  - "die neue RSS-Store-Zahl: 1.837,8 MB anon-Spitze mit aktiver Semantik auf 4 GB ARM, unter der harten 2-GB-Grenze, oom 0"
  - "die gemessene Kennzahl 1.321,0 Byte je Dokument (145.854 Chunks, 2,807 je Dokument), ersetzt 876,0"
  - "die gemessene Embedding-Dauer auf der Zielbox (D-17a): erste Spur 18 h 04 min statt 12 h 49 min, bis zum letzten Vektor 18 h 56 min"
  - "die Grundlast der Semantik im Leerlauf: 595 MB, aufgeschluesselt (Tokenizer 268,8, Chunker 272,8, Gewichte 397,1 bei der ersten Einbettung)"
  - "der Befund fuer die Haertung: die Suchseite laedt eine zweite Modellinstanz, +276 MB dauerhaft, 210 MB Abstand zur harten Grenze"
  - "docs/performance.md, docs/embeddings.md und README.md mit den Zahlen dieses Laufs; die alten Zeilen stehen als Vergleich daneben"
affects: [06-12 Store-Abgabe, Launch-Haertungsphase]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Waechter, der eine Zahl in jeder Runde protokolliert, wird beim Scharfstellen einmal gegen eine bekannte Zahl gelesen"
    - "Ein Skript, das erst am Ende eines langen Laufs faehrt, wird vorher einmal trocken gegen das echte Schema gefahren"
    - "Eine Wartefrist wird gegen die langsamste beteiligte Uhr bemessen, nicht gegen die, an die man gerade denkt"
    - "Der Fertig-Vertrag eines unbeaufsichtigten Laufs ist eine Datei im Dateisystem, die Meldekette ist nur Komfort und protokolliert ihren HTTP-Code"

key-files:
  created:
    - docs/measurements/2026-09-05-semantiklauf-m7g/README.md
    - docs/measurements/2026-09-05-semantiklauf-m7g/semantiklauf.csv
    - docs/measurements/2026-09-05-semantiklauf-m7g/statusseite.jsonl
    - docs/measurements/2026-09-05-semantiklauf-m7g/07-oom-beweis.txt
    - docs/measurements/2026-09-05-semantiklauf-m7g/48-vektorbestand.txt
    - docs/measurements/2026-09-05-semantiklauf-m7g/skripte/
  modified:
    - docs/performance.md
    - docs/embeddings.md
    - README.md

key-decisions:
  - "Kriterium 5 Teil 2 (memory.events mit lauter Nullen) ist NICHT erfuellt (max 2796) und wird so gefuehrt; der Owner hat am 06.09. entschieden, die Store-Aussage auf die drei Schadenszaehler (oom, oom_kill, oom_group_kill, alle 0) plus anon-Spitze zu stellen und max als Kennzahl auszuweisen"
  - "Die Box wird angehalten statt abgebaut (Owner 06.09.), abweichend von Task 4, weil am selben Tag eine Launch-Haertungsphase vor der Abgabe beschlossen wurde und Korpus, Indizes und Abbilder dafuer die schnellste Zielhardware sind"
  - "Die zweite Modellinstanz der Suchseite wird in diesem Plan nicht geaendert, damit die Store-Zahl so gemessen ist, wie das Produkt heute ausgeliefert wuerde; der Fix gehoert in die Haertungsphase"
  - "Der Endungsvergleich der Verdikte gegen den Generator bleibt offen und steht im Bericht als fehlend, nicht als erledigt"

patterns-established:
  - "Phasenspitzen werden an der abgelesenen Grenze der ersten Spur getrennt (letzte Aufnahme mit indexed < Endstand), nicht an einer angenommenen Uhrzeit"
  - "Eine Speicherspitze wird mit dem Ereignis erklaert, mit dem sie zeitlich zusammenfaellt, und die Erklaerung wird im Code nachgewiesen, bevor sie im Bericht steht"

requirements-completed: [SEM-01, SEM-03]

# Metrics
duration: rund 21 h Wanduhr, davon 18 h 56 min unbeaufsichtigter Lauf
completed: 2026-09-06
---

# Phase 6 Plan 11: ARM-Volllauf mit Semantik Summary

**50.000 Dokumente mit Volltext, OCR und Einbettung sind auf der 4-GB-ARM-Box durchgelaufen, ohne OOM und ohne Neustart: 51.961 indexiert und eingebettet, 0 fehlgeschlagen, anon-Spitze 1.837,8 MB unter der harten 2-GB-Grenze, 18 h 56 min bis zum letzten Vektor, 1.321,0 Byte je Dokument gemessen statt 876 gerechnet. Die Grenze wurde eingehalten, aber nicht unberuehrt gelassen (memory.events max 2796), und der Grund dafuer ist ein Befund, der in die Haertung geht: die Suchseite laedt eine zweite Kopie des Modells.**

## Performance

- **Duration:** Anstoss 2026-09-05T10:47:54Z, Ende erkannt 2026-09-06T06:15:09Z, Bericht und Dokumente bis 2026-09-06T07:30Z
- **Tasks:** 4 von 4 (Task 4 als Owner-Abnahme mit zwei Entscheidungen)
- **Files modified:** 3 Dokumente geaendert, ein Messverzeichnis mit 24 Dateien neu
- **Kosten:** 2,37 USD netto fuer 20,5 h Box

## Accomplishments

- **Der Lauf ist bewiesen und nicht behauptet.** Baumhash des Abbilds gleich dem des Arbeitsbaums (`c83b5d7f`), Modellpruefsumme gleich der aus 06-03 (`8da4c9ba`), Korpus bitgleich mit 05-21 (`bcbef9b2`), DI-05-36 in beiden Teilen gemessen (null Poller-Durchgaenge unbewaffnet, vierzehn nach der Registrierung).
- **Beide Spuren getrennt gemessen, aus dem Statusbeobachter abgelesen.** Erste Spur 18 h 04 min (05-21: 12 h 49 min, +41 Prozent durch die Einbettung nebenher bei `INDEX_WORKERS=1`), Nachlauf der zweiten Spur 52 min, rund 43 Dokumente je Minute neben der OCR und rund 170 allein.
- **Die Grundlast der Semantik ist aufgeschluesselt.** 595 MB im Leerlauf vor der ersten Datei, A/B am selben Volumen gegen das Abbild ohne Semantik. Sie gehoert nicht dem Modell: Tokenizer 268,8 MB, Chunker 272,8 MB, die Gewichte kommen mit 397,1 MB erst bei der ersten Einbettung.
- **IDX-08 ist mit einer Ueberraschung belegt.** Die OCR-Phase blieb bei 1.562,7 MB. Die Spitze von 1.837,8 MB liegt in der Phase nur Einbettung und beginnt auf die Sekunde mit der ersten semantischen Suche (05:15:11Z): `api/resources.py` und `worker/poller.py` halten je eine eigene `EmbeddingModel`-Instanz im selben Prozess, die erste Suche laedt Tokenizer und onnxruntime-Sitzung ein zweites Mal, +276 MB dauerhaft, dazu ein zweites Lesen der Wortliste (der Automat selbst ist gecacht; Korrektur 06.09. nach dem 06.1-Research).
- **Die Suche bleibt benutzbar.** p95 1.129 ms waehrend des Nachlaufs, 524 ms danach, Budget 2.500 ms; `memory.current` neben `anon` waehrend der Last steht im Bericht.
- **Die Kennzahl ist gemessen.** 145.854 Chunks fuer 51.961 Dokumente, 2,807 je Dokument, 68.642.504 Byte mit WAL, 1.321,0 Byte je Dokument, 8,74 Prozent des Tantivy-Index; +50,8 Prozent gegen die gerechneten 876,0, weil der Zwei-Chunk-Deckel ein Boden war.
- **Die drei Zusagen aus D-17 sind eingeloest.** (a) Embedding-Dauer als gemessene Zahl mit Hardware in performance.md und embeddings.md, (b) die Abdeckungsaussage steht in README und beiden Store-Texten seit 06-10, (c) die RSS-Zahl der Kernaussage in README.md ist ersetzt, die alten Zahlen stehen als Vergleichszeilen im Messteil.

## Task Commits

1. **Task 1: Box frei, Vorbedingungen bestaetigt** - Owner-Freigabe 05.09., Box neu gestartet, IP und SG nachgezogen (kein Codecommit)
2. **Task 2: Semantik-Abbild, Bewaffnung, Grundlast, Lauf** - `1c3dbee` (feat), `d052658` (docs, Checkpoint), `85f66e6` (docs, Korrektur waehrend des Laufs), `a9f6e78` (docs, Bericht aus den Rohdaten)
3. **Task 3: Die Zahlen einsetzen, die alten ersetzen** - `80e93c1` (docs)
4. **Task 4: Berichtsabnahme und Box-Verbleib** - Owner 06.09. ("nach deinen Empfehlungen"), Box angehalten, `box.env` fortgeschrieben (ausserhalb des Repos)

## Files Created/Modified

- `docs/measurements/2026-09-05-semantiklauf-m7g/README.md` - der Bericht: Umgebung, Beweis des Standes, Korpus, DI-05-36, Neuaufsatz, Grundlast mit A/B und Aufschluesselung, Anstoss mit der zu fruehen Gegenprobe, Korrektur waehrend des Laufs, Ergebnis mit Phasenspitzen, memory.events, zweites Modell, beide Suchlastproben, Byte je Dokument, Verdikte, Verbleib
- `docs/measurements/2026-09-05-semantiklauf-m7g/skripte/` - 15 Skripte des Laufs, englisch kommentiert; `42c-lesen.py` und `42d-bestand.py` in der korrigierten Fassung
- `docs/performance.md` - neuer Abschnitt "Der Semantik-Volllauf: dieselbe Box, mit der zweiten Spur", neue Zeilen in der Uebersichtstabelle, die Store-Zahl in der Trockenlauf/Volllauf-Tabelle, Kostenabschnitt des Semantiklaufs, zweiter Verbleib der Box
- `docs/embeddings.md` - Nachtrag vom 06.09. in Abschnitt 4 (gemessene Kennzahl neben der gerechneten, mit Abweichung), gemessene Dauer auf der Zielbox in Abschnitt 7
- `README.md` - Kernaussage "What it costs in memory, measured" mit den Zahlen des Semantiklaufs, den zwei ehrlichen Saetzen zu `max` und zur zweiten Modellinstanz, die alte Zahl als Vergleich

## Decisions Made

- **Kriterium 5 wird geteilt gefuehrt.** Teil 1 (anon unter 2,0 GB) erfuellt mit 1.837,8 MB. Teil 2 (memory.events lauter Nullen) nicht erfuellt: `max` 2796, weil der Dateicache des Index bei 1,5 bis 1,8 GB anon gegen die 2 GB anlag. Die drei Schadenszaehler stehen auf null, kein Neustart. Der Owner hat entschieden, die Store-Aussage auf Schadenszaehler plus anon-Spitze zu stellen und `max` als Kennzahl auszuweisen; README und performance.md sagen es so.
- **Anhalten statt Abbauen.** Task 4 sah den Abbau mit Nichtexistenz-Pruefung vor. Der Owner hat am 06.09. die Launch-Haertungsphase vor der Abgabe beschlossen; die Box mit Korpus, beiden Indizes und drei Abbildern ist dafuer die schnellste Zielhardware. Angehalten kostet sie rund 0,31 USD je Tag. Der Abbau bleibt Aufgabe der Haertungsphase oder der Abgabe.
- **Kein Fix am zweiten Modell in diesem Plan.** Die Store-Zahl soll das ausgelieferte Produkt messen. Der Befund steht als erster Punkt der Haertungsphase.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Der Waechter las `embedded` aus dem falschen Feld und haette weder die Suchlastprobe gefahren noch das Ende erkannt**

- **Found during:** Task 2, erster Blick am Morgen des 06.09. um 05:12Z, nach 219 Runden mit `indexed=0 embedded=0` im Protokoll
- **Issue:** `42c-lesen.py` suchte beide Zahlen auf der obersten Ebene der Aufnahme; dort steht `indexed` der PHP-Haelfte (per Bauart 0) und `embedded` gar nicht, beide leben unter `backend`. Folge: die Bedingung `embedded > 200` fuer die Suchlastprobe im Nachlauf war nie wahr, und die Endeerkennung haengt an `SUCHLAST_GEFAHREN=1`; der Waechter waere erst am Deckel von 340 Runden, rund neun Stunden nach dem echten Ende, in den Abschluss gelaufen.
- **Fix:** Suchlastprobe um 05:15:09Z von Hand gestartet, waehrend die zweite Spur noch lief (Vorrat 4.775); Leser auf der Box gepatcht (Original als `.orig`), alter Waechter per PID beendet, `42b-wachter-neu.sh` mit `SUCHLAST_GEFAHREN=1` neu gestartet. Der neue Waechter las in Runde 1 richtig und hat das Ende regulaer erkannt, den OOM-Beweis erhoben und den Vektorbestand gemessen.
- **Files modified:** docs/measurements/2026-09-05-semantiklauf-m7g/skripte/42c-lesen.py, README des Berichts (Abschnitt "Die Korrektur waehrend des Laufs")
- **Verification:** Waechterlog ab 05:15:09Z mit `embedded=47186`, `00-ende.txt` und `07-oom-beweis.txt` vom Waechter geschrieben, `00-FERTIG` um 06:20:32Z
- **Committed in:** `85f66e6`

**2. [Rule 1 - Bug] `42d-bestand.py` fragte eine Spalte `verdict`, die `state` heisst**

- **Found during:** Task 2, Abschluss des Waechters um 06:15:33Z, Traceback in `48-vektorbestand.txt`
- **Issue:** `sqlite3.OperationalError: no such column: verdict`; die Groessen des Datenspeichers waren geschrieben, die Zaehlung von Chunks, Dokumenten und Byte je Dokument fehlte.
- **Fix:** Spaltenname korrigiert, Skript um 06:39:49Z am unveraenderten Container nachgefahren (Container seit 05.09. 10:44:39Z nicht neu gestartet, also gilt die Messung als "nach dem Lauf, vor jedem Eingriff" weiter).
- **Files modified:** docs/measurements/2026-09-05-semantiklauf-m7g/skripte/42d-bestand.py, 48-vektorbestand.txt (Nachmessung angehaengt)
- **Committed in:** `a9f6e78`

**3. [Rule 3 - Blocker] SSH zur Box blockiert, weil die Security-Group-Regel an der Owner-IP haengt**

- **Found during:** Task 2, Morgen des 06.09.
- **Issue:** Die Owner-IP hatte gewechselt (77.3.92.37 nach 77.3.232.67), Port 22 war nur fuer die alte offen.
- **Fix:** Regel per revoke und authorize nachgezogen, in `box.env` notiert.
- **Verification:** ssh erfolgreich um 05:12:52Z

### Abweichungen mit Owner-Entscheid

- **Task 4, Box-Abbau:** nicht abgebaut, sondern angehalten (siehe Decisions Made). Die Nichtexistenz-Pruefung entfaellt damit fuer diesen Plan.
- **Task 2, Acceptance "memory.events zeigt fuer jeden Zaehler 0":** nicht erreicht, im Bericht als nicht erfuellt gefuehrt, Bewertung durch den Owner (siehe Decisions Made).
- **Task 2, Acceptance "Verdikte passen zur Verteilung des Generators":** nicht gemacht, im Bericht als fehlend benannt.

## Issues Encountered

- Die ntfy-Meldekette antwortete beim Scharfstellen mit 403 (Box hatte eine neue Adresse) und beim Abschluss mit 200. Der Fertig-Vertrag war deshalb von Anfang an die Datei `00-FERTIG`; die Meldung kam trotzdem an.
- Die Gegenprobe des Startskripts hat den Lauf um 52 Sekunden zu frueh fuer tot erklaert (Wartefrist gegen den Poller-Rueckzug bemessen statt gegen den Fuenf-Minuten-Cron von AIO). Im Bericht dokumentiert, Skript unveraendert, damit der Fehler lesbar bleibt.
- `memory.peak` der cgroup liess sich nicht zuruecksetzen und traegt die Vorbereitungsmessungen mit; die tragende Zahl ist `anon` aus der Samplerreihe, wie in 05-21.

## Next Phase Readiness

- **Nicht direkt 06-12.** Owner-Regel vom 06.09.: vor der Store-Abgabe kommt eine Launch-Haertungsphase mit ausgiebigen Tests jenseits des Happy Path. Sie wird per `/gsd:phase` vor 06-12 eingefuegt und geplant.
- **Erster Punkt der Haertung:** eine gemeinsame Embedding-Engine fuer Suchseite und Arbeiter oder ein Entladen der Suchseite nach Leerlauf (+276 MB, 210 MB Abstand zur Grenze). Danach Nachmessung auf der angehaltenen Box.
- **Offen aus diesem Plan:** Endungsvergleich der Verdikte; Abbau der Box mit Nichtexistenz-Pruefung am Ende der Haertung oder der Abgabe; `APPSTORE_TOKEN` vor der ersten Einreichung rotieren.
- **Beim naechsten Start der Box:** IP wechselt, `BOX_IP`, SG-22 auf die Owner-IP und `loadtest.infranode.dev` nachziehen, Container ueber AppAPI neu bewaffnen (DI-05-36).

---
*Phase: 06-semantische-suche*
*Completed: 2026-09-06*
