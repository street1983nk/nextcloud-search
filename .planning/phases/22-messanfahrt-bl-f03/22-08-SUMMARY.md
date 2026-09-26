---
phase: 22-messanfahrt-bl-f03
plan: 08
subsystem: messanfahrt
tags: [box, aufbau, unbeaufsichtigt, timer, v13, tor-abbruch, wiedereinstieg]
requires:
  - "22-07 (Freigabe 26.09.2026, Laufwerte 1354 / 86 / ja / a, Box-Digest-Kandidat)"
provides:
  - "Box nach Runbook aufgebaut, Rohdaten von P0 bis 92c, 00-FERTIG mit b4 vorbereitet"
  - "Box gestoppt für 22-09 (B4, Abbau), Grub-Drop-in mem=4G entfernt"
  - "Sollwert des Snapshots 52137 / 44 / 6 (Owner-Entscheid), E2 und E3 neu gefasst"
  - "00-lauf.sh ab-pii, 92e mit Netzaliasen, 95c mit Suchkonto"
affects:
  - "22-09 (B4 nach dem Merksatz: nach jedem Maschinenstart erst bewaffnen, dann messen)"
  - "22-10 (MESS-09 aus 98d-dismax-probe.txt, Sprachfall-Dateien im Bestand)"
  - "22-11 (Bericht: Lücke Kaltstartlatenz, Befunde 94c 32 und B5 50)"
tech-stack:
  added: []
  patterns:
    - "Timer absolut per shutdown -h HH:MM statt +N, weil +N auf die Minute rundet und den Deckel um bis zu 59 s überzieht"
    - "Wiedereinstieg eines unbeaufsichtigten Laufs als eigener Unterbefehl, der die Tore kurz prüft und nur die fehlenden Blöcke fährt"
    - "Antwortkriterium je Zustand: im Umbau rebuildTotal > 0, in Ruhe languagesActive gesetzt und embedded > 0"
key-files:
  created:
    - docs/measurements/2026-09-v13-messung/rohdaten/01-aws-lesende-proben.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/02-vorbedingungen.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/03-aufbau.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/04-wiederanlauf.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/00-typwechsel.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/00-lauf.txt
    - docs/measurements/2026-09-v13-messung/rohdaten/00-FERTIG
    - docs/measurements/2026-09-v13-messung/rohdaten/lauf1-tor41/
    - docs/measurements/2026-09-v13-messung/rohdaten/ab-pii-92d/
  modified:
    - docs/measurements/2026-09-v13-messung/README.md
    - docs/measurements/2026-09-v13-messung/skripte/00-ablauf.md
    - docs/measurements/2026-09-v13-messung/skripte/00-lauf.sh
    - docs/measurements/2026-09-v13-messung/skripte/92d-wechsel.sh
    - docs/measurements/2026-09-v13-messung/skripte/92e-umgebung.sh
    - docs/measurements/2026-09-v13-messung/skripte/95c-kaltstart.sh
    - docs/measurements/2026-09-v13-messung/skripte/90e-einzelliste.py
    - backend/tests/test_v13_ablauf.py
    - backend/tests/test_v13_wechsel.py
    - .planning/phases/22-messanfahrt-bl-f03/22-08-PLAN.md
decisions:
  - "Owner 26.09.2026 ('wie deine empfehlung'): Sollwert des Snapshots 52137 / 44 / 6 in 92d und 00-lauf.sh; E2 und E3 neu gefasst, weil der Snapshot die 39 Sprachfall-Dateien vom 10.09. enthält"
  - "Owner 26.09.2026 ('ja bitte'): Fix für Tor 58 (embedded erst aus einer beantworteten Statuszeile), Wiedereinstieg ab PII, 95c unter lasttest, 99d nach Vorrat 0"
  - "Koordinator im Rahmen der Freigabe, Option A: Bewaffnung nach Maschinenstart nachholen, 92e trägt Netzaliase, Rückweg mit eigenem Antwortkriterium"
  - "Box-Klon auf dem jeweils gepushten Kopf statt auf 59f05fe; backend/src und php sind seit dem Digest-Commit unverändert, der Beweis bleibt der Baumhash"
metrics:
  duration: "ca. 8 h 20 min Wand (04:56Z bis 13:15Z, mit rund 5 h Pause bei gestoppter Box)"
  completed: 2026-09-26
  tasks: 3
  files: 20
---

# Phase 22 Plan 08: Aufbau, unbeaufsichtigte Anfahrt und Rohdaten bis zur Selbstabschaltung Summary

Die Box ist nach Runbook entstanden und hat nach drei Tor-Abbrüchen mit Owner- beziehungsweise Koordinator-Entscheiden und vier Werkzeug-Fixes den Ablauf regulär beendet: `00-FERTIG` um 13:06:26Z mit `b4 vorbereitet`. Danach hat sie sich nach der letzten Abholung selbst abgeschaltet. Der Timer stand fest absolut auf 2026-09-27T03:33:00Z und wurde nie erreicht. Der m7g.large-Teil kostete 2,02 Boxstunden und 0,232 USD. Alle Rohdaten sind committet und gepusht.

## Aufgaben

| Task | Name | Commits | Ergebnis |
| ---- | ---- | ------- | -------- |
| 1 | Vorbedingungen und Aufbau, Blöcke 1 bis 13 | 110838d | 15 Vorbedingungen, Blöcke 1 bis 13 gestempelt, `shutdown-verhalten stop` |
| 2 | Ablauf starten, Abholen, erste Tore | 110838d, 6fa85a4, 26e5e8f, f513f74 | Fahrt 1: Tor 41 (Snapshot trägt 52137 / 44 / 6), Sollwert per Owner-Entscheid umgestellt; Fahrt 2: 92d 0, Bestandstor bestanden |
| 3 | Einsammeln bis zur Selbstabschaltung | ac521ff, aecca7d, 55acdc0, e75a55c, be35cfe, 88783b9, 65f8399, 381c946 | Tor 58, zweimal Tor 59, Befund 92e; dritter Anlauf ab PII regulär bis 00-FERTIG |

## Verlauf der Tore

| Tor | Ursache | Behebung |
|---|---|---|
| 41, Fahrt 1 | Der Snapshot trägt 52137 / 44 / 6 (39 Sprachfall-Dateien mitindexiert), das Tor erwartete 52111 / 37 / 0 | Owner-Entscheid, Sollwert in 92d und 00-lauf.sh (26e5e8f) |
| 58, Fahrt 2 | Erste Statuszeile 4 s nach dem Containerstart, `embedded 0` vor der Antwort des Backends | Kriterium `rebuildTotal > 0` in `block_umbau`, Wiedereinstieg `ab-pii` (aecca7d) |
| 59, ab-pii 1 | Bewaffnung nach dem Maschinenstart ausgelassen, dazu 92e ohne Netzalias (HaRP: `Cannot resolve 'findling_backend'`) | 92e trägt Aliase (be35cfe), 92d von Hand, Bewaffnung mit Beleg `backendReachable True` |
| 59, ab-pii 2 | Das Kriterium aus aecca7d gilt nur im Umbau, im Ruhezustand ist `rebuildTotal` 0 | `backend_antwortet_in_ruhe` für den Rückweg (65f8399) |

## Messstand (Auswertung in 22-10 und 22-11)

- M-01: fünf Laststufen gefahren. Bodensatz `zyklus2-minus-c1 30.5` MB. 99d wiederholt mit 0. 92c 36 und 0. Die Einzelliste nennt 50 Dateien.
- MESS-08: Index de,en 786.508.818 Byte, sechs Felder 1.431.953.684 Byte, Umbau-Wandzeit 581 s.
- MESS-09: 98d mit 0, und die Sprachfall-Dateien stehen im Bestand (MESS-09-Risiko aus 22-07 entfällt).
- B1 mit 16 Containerleben, B2 und B3 gefahren, B5 Befund 50 (RAM-Abtaster ohne Abtastung), B4 vorbereitet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Klon auf dem gepushten Kopf statt auf dem Digest-Commit**
- **Found during:** Task 1
- **Issue:** 59f05fe hat den 92d-Fix bbf929e noch nicht.
- **Fix:** Klon auf dem gepushten Kopf. `backend/src` und `php` sind unverändert, begründet in 02-vorbedingungen.txt.

**2. [Rule 2 - Missing] shutdown-Verhalten ausdrücklich gesetzt**
- **Found during:** Task 1, Block 3
- **Fix:** `--instance-initiated-shutdown-behavior stop` in run-instances.

**3. [Rule 3 - Blocking] Passwortdateien und 401**
- **Found during:** Task 1, Block 9 und 10
- **Issue:** Die Sicherung trägt kein .pw, und die Passwörter der v1.2 passten nicht zum Snapshot.
- **Fix:** .pw aus konten.env angelegt, `occ user:resetpassword` mit dem Wert nur über stdin.

**4. [Rule 3 - Blocking] Negativer DNS-Cache der VPC**
- **Found during:** Task 1, Block 10
- **Fix:** Abgewartet (rund 3 min), kein Pin. Lehre im Protokoll: den Record vor dem ersten Daemon-Start setzen.

**5. [Rule 1 - Bug] Timer um Sekunden über dem Deckel**
- **Found during:** Task 3
- **Issue:** `shutdown +N` rundet auf die Minute, der Timer lag bis zu 48 s über dem Deckel.
- **Fix:** Nach jedem Start absolut `shutdown -h 03:33` gesetzt und zurückgelesen.

**6. [Rule 1 - Bug] Artefakt-Gate**
- **Found during:** Task 1
- **Fix:** PEM-Kopfzeile, AMI- und Snapshot-Kennung in den handgeschriebenen Protokollen durch Platzhalter ersetzt.

Die Werkzeugänderungen 26e5e8f, aecca7d, be35cfe und 65f8399 liefen jeweils über einen Checkpoint mit Entscheid (siehe 22-08-PLAN.md, `checkpoint_result` 1 bis 4). Vor jedem Commit waren die Gates grün: ruff, format, pyright latest, vulture und die volle Suite, zuletzt 3272 passed.

## Deferred Issues

- **Kaltstartlatenz mit Trefferpflicht: Lücke.** 95c endete unter `admin` und unter `lasttest` mit 48. Kalt kamen 0 Treffer bei rund 1,8 bis 2,1 s, warm unter `lasttest` 26 Treffer. Die M-01-Gegenprobe ist damit nicht entschieden. Die Ursache ist offen, zur Auswertung in 22-10/22-11.
- 94c: `abtastreihe-spitze-mb` unlesbar (32). B5: RAM-Abtaster ohne Abtastung (50).
- Die Prüfsummen der gefahrenen Fassungen (00-ablauf.md, Abschnitt 5) fallen nach dem Lauf an. Die Werkzeuge sind in dieser Anfahrt mehrfach geändert worden, und die Prüfsumme gehört auf die zuletzt gefahrene Fassung (65f8399).
- Im Box-Klon sind die fünf handgeschriebenen Protokolle entfernt, damit das Abholen sie nicht überschreibt. 22-09 muss das beim Typwechsel beachten.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: rohdaten/00-FERTIG, 00-lauf.txt, 03-aufbau.txt (Blöcke 1 bis 13, je Start und Ende), 00-typwechsel.txt (`shutdown-verhalten stop`)
- FOUND: README Abschnitt 6.6 Laufende
- FOUND: 110838d, 6fa85a4, 26e5e8f, f513f74, ac521ff, aecca7d, 55acdc0, e75a55c, be35cfe, 88783b9, 65f8399, 381c946
- Instanz stopped, test_public_artifacts.py grün, v1.2- und Nachfolgeverzeichnis unverändert
