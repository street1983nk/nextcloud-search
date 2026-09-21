---
phase: 12-messwerkzeug-runbook-und-terminentscheid
plan: 08
subsystem: docs
tags: [runbook, messbedingung, cron, abbau, kosten, aws, ebs, mess-04, mess-06]

# Dependency graph
requires:
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: "docs/runbook-messbox.md Abschnitte 1 bis 5 aus Plan 12-07 (Form, Deckel-Rechenblatt, Abbruchzeile der Zustandspruefung)"
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: "97-cron-vorpruefung.sh mit beiden Zweigen und 00-ablauf.md mit der Abbruchtabelle aus Plan 12-06"
provides:
  - "docs/runbook-messbox.md, Abschnitte 6 bis 9: fuenf protokollpflichtige Vergleichbarkeitsgroessen mit Sollwerten, neun Messschritte mit Abbruchpfad, neunschrittige Abbau-Checkliste, Kostenfuehrung ueber box.env"
  - "Die vollstaendige Rueckgabewert-Tabelle 15 bis 19 und 22 bis 28 im Runbook, im Gleichschritt mit 00-ablauf.md"
  - "Die Regel, dass waehrend der bezahlten Anfahrt kein Werkzeug mehr geaendert wird"
affects: [15-messphase-eine-box-anfahrt, 14-modell-entladung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Messbedingung steht mit ihrem Sollwert und ihrer Ablesestelle in einer Tabelle, nicht als Satz im Fliesstext; ohne Sollwert ist eine Bedingung nur eine Bitte"
    - "Die Abbau-Reihenfolge ist selbst die Aussage: erst erheben, dann sichern, dann pruefen, dann zerstoeren, danach nachsehen"
    - "Jeder Messschritt traegt seinen Abbruchpfad in derselben Zeile wie sein Werkzeug und seine Rohdatei"

key-files:
  created: []
  modified:
    - docs/runbook-messbox.md

key-decisions:
  - "Abschnitt 7 ordnet nach dem Zeitpunkt des Starts und nicht nach der Zaehlung von 00-ablauf.md; die dortigen Schrittnummern stehen in Klammern daneben, damit der Gleichschritt pruefbar bleibt"
  - "Die Rueckgabewerte der Tabelle stehen ohne Fettschrift, weil die Pruefung des Plans die Zahl mit folgendem Leerzeichen sucht; der Textfluss traegt die Bedeutung stattdessen im Nachsatz"
  - "Der Tag-Sweep steht mit BEIDEN Tagwerten im Runbook, obwohl aws_box.sh restore seit 12-03 selbst umtaggt: ein von Hand aus dem Snapshot erzeugter Datentraeger haette dieselbe Falle"
  - "Abschnitt 9.4 benennt die ungefahrenen Stellen und legt fest, dass eine Abweichung beim Erstvollzug als eigene Zeile stehen bleibt statt still ueberschrieben zu werden"

patterns-established:
  - "Ein oeffentliches Betriebsrunbook nennt Feldnamen und Pfade der Kostenfuehrung, aber keine Werte: Kennungen und Adressen bleiben Platzhalter"

requirements-completed: [MESS-04, MESS-06]
requirements-advanced: []

# Metrics
duration: 20min
completed: 2026-09-14
---

# Phase 12 Plan 08: Runbook der Messbox, Abschnitte 6 bis 9 Summary

**Das Runbook ist vollstaendig: fuenf Messbedingungen werden abgelesen statt erinnert, jeder der neun Messschritte nennt seinen Abbruchpfad mit Rueckgabewert, und der Abbau erhebt seine Zahlen und sichert seine Historie, bevor er das erste Mal etwas zerstoert.**

## Performance

- **Duration:** rund 20 min
- **Started:** 2026-09-14T17:25Z
- **Completed:** 2026-09-14T17:45Z
- **Tasks:** 2 von 2
- **Files modified:** 1 (`docs/runbook-messbox.md`, von 613 auf 1.008 Zeilen)

## Accomplishments

- **Abschnitt 6** macht fuenf Groessen protokollpflichtig, jede mit Ablesestelle, Begruendung und Sollwert: Zeilenstaende (52.111 / 37 / 0), Cron-Intervall (300 s, Toleranz zehn Prozent), Instanztyp und Containergrenze (m7g.large, `2147483648`), Zeit seit dem letzten Containerstart (ohne Sollwert, weil der Abstand die Aussage ist) und Werkzeugstand als Baumhash.
- **Abschnitt 6.1** nennt die drei Protokollzeilen des Konfigurationszweiges (`cron-modus-ist`, `cron-intervall-quelle`, `cron-intervall-ist`) mit den Rueckgabewerten 25 und 26 und sagt, warum eine Checkliste dafuer nicht reicht.
- **Abschnitt 6.2** nennt die sechs Zeilen des Wirkungszweiges und schreibt ausdruecklich hin, dass das Protokoll die Ablesereihe benennen muss, aus der die Prozentzahl stammt: in v1.1 haben 194 von 812 gegen 62 von 325 Lesungen rund 24 gegen 19 Prozent fuer denselben Sachverhalt ergeben.
- **Abschnitt 6.3** haelt Vollkorpus (D-04), Zielinstanz m7g.large (D-06) und das unangetastete `scripts/ops/search_load.py` fest, jeweils mit dem Satz, was die Abweichung kosten wuerde.
- **Abschnitt 7** fuehrt neun Messschritte mit Werkzeug, Rohdatei und Abbruchpfad, dazu die vollstaendige Tabelle der zwoelf Rueckgabewerte 15 bis 19 und 22 bis 28 und den Schlusssatz, dass waehrend der bezahlten Anfahrt kein Werkzeug mehr geaendert wird.
- **Abschnitt 8** ist die neunschrittige Abbau-Checkliste mit je einem Kommandoblock und einer Zeile `Erwartete Ausgabe`: Endmessungen, Historie fortschreiben, `stop` und `snapshot`, unabhaengige Nachlese mit sechs Feldern, Sicherung und `FINDLING_STATE_BACKUP`, `destroy`, Tag-Sweep ueber beide Tagwerte, Kostenueberblick, und was bewusst stehen bleibt.
- **Abschnitt 9** fuehrt dreizehn `box.env`-Felder mit Schreibzeitpunkt und Schreiber, begruendet den Ort der Zustandsdatei ausserhalb des Arbeitsbaums, beschreibt den Rueckfluss in die Ist-Spalte des Deckel-Rechenblatts (D-05) und benennt zum Schluss, was das Runbook nicht leisten kann.
- Die Geheimnisregel haelt ueber die neuen 395 Zeilen: kein IPv4-Muster, keine lebende Instanz-, Volume- oder Gruppenkennung, keine Kontokennung. Beide `<automated>`-Bloecke des Plans melden GRUEN.

## Task Commits

1. **Task 1: Abschnitte 6 und 7, Vergleichbarkeitsbedingungen und Messreihenfolge** - `24c2776` (docs), 128 Zeilen
2. **Task 2: Abschnitte 8 und 9, Abbau-Checkliste und Kostenfuehrung** - `9f88453` (docs), 267 Zeilen

**Plan metadata:** siehe Schlusscommit dieses Plans (docs)

## Files Created/Modified

- `docs/runbook-messbox.md` (geaendert, 613 auf 1.008 Zeilen) - Abschnitte 6 bis 9 ergaenzt; die Abschnitte 1 bis 5 aus Plan 12-07 sind unveraendert

## Decisions Made

- **Abschnitt 7 ordnet nach dem Startzeitpunkt, nicht nach der Zaehlung von `00-ablauf.md`.** Der Plan gibt die Reihenfolge Volllauf, Wirkungszweig, Laststufen, Sprachfall vor; `00-ablauf.md` zaehlt den Sprachfall als Schritt 4 und den Wirkungszweig als Schritt 5, weil dort die Beweise gezaehlt werden. Beide laufen neben dem Volllauf, aber der Wirkungszweig wird mit ihm gestartet. Im Runbook steht die Startreihenfolge, jede Zeile traegt die Schrittnummer aus `00-ablauf.md` in Klammern, und ein eigener Absatz erklaert den Unterschied. Werkzeuge, Rohdateien und Rueckgabewerte sind in beiden Dateien dieselben.
- **Die Rueckgabewerte stehen ohne Fettschrift.** Die automatisierte Pruefung des Plans sucht jede der zwoelf Zahlen mit folgendem Leerzeichen. `**16**` haette sie nicht gefunden, und die Zahl haette in einer Tabelle gestanden, die ihre eigene Pruefung nicht besteht. Jede Zeile lautet deshalb "Rueckgabewert 16 fuer den nicht geleerten Vorrat" und traegt die Bedeutung im Nachsatz statt in der Auszeichnung.
- **Der Tag-Sweep bleibt zweiteilig, obwohl `restore` seit Plan 12-03 selbst umtaggt.** Die Umtaggung mit Rueckleseprobe im Skript deckt den Pfad ueber `aws_box.sh restore` ab. Ein von Hand aus dem Snapshot erzeugter Datentraeger erbt `purpose=findling-corpus-keep` genauso und entginge dem Sweep von `cmd_destroy`. Der Schritt fragt deshalb beide Tagwerte und nennt den Grund; die zweite Suche ist zugleich der Beweis, dass der Snapshot den Abbau ueberlebt hat.
- **Vier Schritte der Abbau-Checkliste tragen keine Marke fuer den Erstvollzug, fuenf schon.** Nicht markiert sind die Schritte 3 bis 6 und 8, weil Snapshot, Nachlese, Sicherung, `destroy` und Kostenueberblick am 11.09.2026 tatsaechlich gefahren worden sind und ihre Ausgaben in `07-snapshot-und-abbau.txt` stehen; die erwarteten Ausgaben zitieren diesen Lauf mit Fundstelle. Markiert sind die Schritte 1 und 2, weil die Endmessungen einer v1.2-Anfahrt und die Uebernahme ihrer Historie in dieser Form noch nicht gefahren sind.
- **Abschnitt 9.4 legt fest, was nach dem Erstvollzug mit den erwarteten Ausgaben geschieht.** Sie werden durch die tatsaechlichen ersetzt, aber eine Abweichung bleibt als eigene Zeile stehen. Ein Runbook, das seine eigenen Irrtuemer loescht, lehrt beim zweiten Mal dasselbe wie beim ersten.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Die Rueckgabewert-Tabelle bestand die eigene Pruefung des Plans nicht**

- **Found during:** Task 1, nach dem ersten Schreiben des Abschnitts 7
- **Issue:** Die zwoelf Rueckgabewerte standen als `**15**` bis `**28**`. Die `<automated>`-Pruefung des Plans sucht `| <zahl> ` oder `<zahl> `, also die Zahl mit folgendem Leerzeichen. Sechs der zwoelf Werte (16, 18, 22, 23, 27, 28) fielen durch, weil auf die Zahl unmittelbar Sternchen folgten.
- **Fix:** Die Tabellenspalte "Folge" nennt die Zahl schlicht und setzt einen erlaeuternden Nachsatz daneben ("Rueckgabewert 22 fuer die fehlende Laufnummer"). Die Auszeichnung entfaellt, die Aussage nicht.
- **Files modified:** docs/runbook-messbox.md
- **Verification:** die Schleife ueber alle zwoelf Werte meldet keinen Fehlschlag mehr, der ganze Block meldet GRUEN
- **Committed in:** 24c2776

---

**2. [Rule 2 - Missing critical] Die Abbau-Checkliste haette lebende Ressourcenkennungen getragen**

- **Found during:** Task 2 (Schritte 6 und 7)
- **Issue:** Die Vorlage des tatsaechlich gefahrenen Abbaus vom 11.09.2026 nennt Instanz, beide Datentraeger und die Security Group mit ihren Kennungen, dazu die Kontokennung im Feld `OwnerId` der Nachlese. Alle vier waeren mit einem Kopieren des Rezepts in eine oeffentliche Datei gewandert und haetten die Geheimnisregel dieser Datei gerissen (T-12-40).
- **Fix:** Die Kommandobloecke arbeiten ohne Kennungen: `aws_box.sh destroy` nimmt sie aus `box.env`, die Tag-Suchen brauchen keine, und wo eine Kennung im Text noetig war, steht `<instanz>`, `<volume>` oder `<sg>` nach dem Muster der Platzhaltertabelle aus Abschnitt 4. Die Nachlese nennt die sechs Felder, nicht ihre Werte; `OwnerId` gehoert bewusst nicht dazu. Die Snapshotkennung bleibt als einzige im Klartext, wie im Kopf der Datei begruendet.
- **Files modified:** docs/runbook-messbox.md
- **Verification:** `grep -E '\b(i-|vol-|sg-|sgr-)[0-9a-f]{8,}\b|\b[0-9]{12}\b'` findet in den neuen Abschnitten nichts; das IPv4-Muster ebenfalls nicht
- **Committed in:** 9f88453

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 fehlender Pflichtteil)
**Impact on plan:** Kein Scope-Zuwachs. Die erste Abweichung macht eine Tabelle pruefbar, die zweite setzt die Geheimnisregel durch, die der Plan in seinem Threat Model selbst verlangt.

## Issues Encountered

- **Der Gleichschritt mit `00-ablauf.md` ist eine Zuordnung und keine Gleichheit.** Die neun Schritte des Runbooks decken die Anfahrt als Ganzes ab, die fuenf Schritte des Ablaufplans nur die Beweiskette der beiden Messwerkzeuge und der einen Messbedingung. Die Zuordnung steht als eigener Absatz unter der Tabelle; wer sie nicht liest, koennte die abweichende Nummerierung fuer einen Widerspruch halten.
- **Die Rohdateinamen der Schritte 4, 6, 8 und 9 sind Vorgaben und keine Belege.** Fuer Volllauf, Laststufen, Wiederaufwaerm-Messung und Endmessungen gibt es im v1.2-Laufverzeichnis noch keine Dateien; die Namen folgen dem Muster der Vergleichsmessung (`96-volllauf.csv`, `95-*.json`, `90-bestand.txt`). Die Werkzeuge stehen als "Muster von" da, weil sie in diesem Verzeichnis noch nicht liegen.
- **Der MEM-01-Schalter existiert noch nicht.** Schritt 8 der Messreihenfolge haengt an einer Funktion, die in Phase 14 gebaut wird; der Variablenname ist dort ein eigener Entscheid. Das Runbook nennt deshalb den Schalter und nicht die Variable.
- **Gates:** keine gefahren und keine noetig. Dieser Plan hat genau eine Datei unter `docs/` geaendert, keinen Python- oder Shell-Code angefasst und `backend/tests/test_measurement_scripts.py` nicht beruehrt. Geprueft wurden beide `<automated>`-Bloecke des Plans, die Abwesenheit von Wagenruecklaeufen, das IPv4-Muster, lebende Ressourcenkennungen und das Vokabular-Gate.

## Known Stubs

Keine. Die Marke `in Phase 15 erstmals vollzogen` ist kein Stub, sondern eine Aussage ueber den Belegstand: sie steht dort, wo eine erwartete Ausgabe aus einem Skript oder einem frueheren Lauf abgeleitet und nicht gegen diese Kette gefahren worden ist. Abschnitt 9.4 sagt, was beim Erstvollzug mit ihr geschieht.

## Requirements

- **MESS-04 erfuellt.** Die Anforderung nennt drei Teile, und alle drei liegen in dieser Phase vor: die Fremdbestands-Vorpruefung misst seit Plan 12-04 und 12-05 ueber `ranked_sides` statt ueber die gedeckelte OCS-Route, `aws_box.sh` kann seit Plan 12-03 einen Datentraeger aus `snap-03f1d1d9ad9262704` erzeugen und taggt ihn um, und `docs/runbook-messbox.md` liegt mit diesem Plan vollstaendig vor. Der Satzbau der Anforderung verlangt, dass Werkzeug und Runbook VOR der bezahlten Anfahrt stehen, nicht dass die Anfahrt stattgefunden hat.
- **MESS-06 erfuellt.** Die Anforderung verlangt, dass das Cron-Intervall vor jedem Messlauf protokolliert wird und dass die Vergleichbarkeitsbedingungen im Runbook stehen. Das Protokollieren ist seit Plan 12-06 im Skript fail-closed durchgesetzt (Pflichtzeile `cron-intervall-ist`, Abbrueche 25 bis 28), die Bedingungen stehen seit diesem Plan in Abschnitt 6. Die Zuordnungs-Anmerkung in `REQUIREMENTS.md` sagt das ausdruecklich: MESS-06 liegt in Phase 12, weil es Runbook- und Werkzeugarbeit ist; die Anwendung erfolgt im Messlauf der Phase 15 und zaehlt dort unter MESS-05.
- **HART-03 bleibt offen.** Der stable35-Fenster-Entscheid wird am 16.09.2026 von Plan 12-02 vollzogen; erst dieser Vollzug erfuellt die Anforderung.

## User Setup Required

Keine fuer diesen Plan. Fuer Phase 15 bleiben die beiden Owner-Handlungen aus Abschnitt 3 des Runbooks bestehen: der Zugang zur DNS-Verwaltung fuer den A-Record und die Freigabe des Deckels mit Datum (42 h / 4,90 USD netto, Untergrenze 31 h / 3,59 USD).

## Next Phase Readiness

- Das Runbook ist vollstaendig und traegt beide Haelften der Anfahrt: Aufbau und Messung in den Abschnitten 1 bis 7, Abbau und Kostenfuehrung in den Abschnitten 8 und 9. Phase 15 faehrt es woertlich und ersetzt dabei die erwarteten Ausgaben der markierten Bloecke durch die tatsaechlichen.
- Offen in Phase 12 bleibt allein Plan 12-02: der stable35-Vollzug am 16.09.2026 nach der siebenschrittigen Checkliste in `12-STABLE35-ENTSCHEID.md`.
- Der Exit-Code-Katalog des v1.2-Laufverzeichnisses steht unveraendert bei 28; dieser Plan hat keinen neuen Rueckgabewert vergeben, sondern die vorhandenen zwoelf in das Runbook uebernommen.
- Phase 14 bekommt aus Abschnitt 7 eine Vorgabe mit: die Wiederaufwaerm-Messung braucht die protokollierte Zeit seit dem letzten Containerstart, sonst ist der A/B-Vergleich warm gegen kalt nicht einzuordnen.

## Self-Check: PASSED

- `docs/runbook-messbox.md` existiert, 1.008 Zeilen, keine Wagenrueckläufe.
- Beide Commit-Kennungen sind in `git log` auffindbar: `24c2776` und `9f88453`.
- Beide `<automated>`-Bloecke des Plans melden GRUEN.
- `grep -c '^### Schritt '` liefert 9, `grep -c 'Erwartete Ausgabe'` liefert 23 (dreizehn Aufbaubloecke, die Zustandspruefung, acht Schritte des Abbaus, der erklaerende Satz in Abschnitt 4).
- Vokabular-Gate: `grep -in "archiv"` liefert nichts. Kein IPv4-Muster, keine lebende Instanz-, Volume- oder Gruppenkennung, keine Kontokennung, kein U+2014, kein U+2013, keine Emojis.

---
*Phase: 12-messwerkzeug-runbook-und-terminentscheid*
*Completed: 2026-09-14*
