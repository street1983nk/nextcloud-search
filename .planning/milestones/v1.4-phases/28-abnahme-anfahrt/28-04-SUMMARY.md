---
phase: 28-abnahme-anfahrt
plan: 04
subsystem: messung
tags: [abnahme-anfahrt, runbook, x86, vorprobe, abbau, mess-10]
requires:
  - "28-01: 02-rechenblatt.py deckel/stand, 00-ablauf.md"
  - "28-02: 00-kette.sh, 10-zelle.sh, 11-probe-route.py, 93b-nullstand.sh"
  - "28-03: aws_box.sh Satztabelle und geteilte Gruppe, 00-typwechsel.sh"
provides:
  - "Runbook: Sätze der sechs Typen, NEU-Posten, Deckel in USD je Box-Satz (58,74 USD, mit Anker 59,43 USD)"
  - "Runbook Block 7b (fio-Initialisierung), Block 14 (x86-Box c7a mit Machbarkeitstor 1 h 30), Nachträge Block 5/12"
  - "Runbook 7.3 Matrix-Anfahrt: Kette, Zelle, Deckelregel D-28-02, Sicherheitstimer D-28-14, jeder Schritt mit Werkzeug"
  - "Runbook Abschnitt 8: Gruppe erst beim zweiten Abbau, Schritt 6b Snapshot-Löschung nach SC4, Sweep 17 Regionen, 0 Snapshots"
  - "Rohdatei 00-vorprobe-x86.txt: vorprobe-ergebnis postgres ja abbilder ja"
affects: [28-05, 28-08]
tech-stack:
  added: []
  patterns:
    - "Runbook-Änderungen nur als datierte Nachträge und neue Blöcke, kein Umformulieren bestehender Absätze"
    - "Regionen-Sweep als Zählung (length(...)), damit die Ausgabe ohne Kennungen in die Rohdatei darf"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/00-vorprobe-x86.txt
  modified:
    - docs/runbook-messbox.md
decisions:
  - "Vorprobe mit postgres:18.6 (Tag gleich der AIO-Fassung) und busybox:1.37 statt alpine, damit kein lokal genutzter Tag umgebogen wird"
  - "Vorprobe prüft amcheck VOR und NACH REINDEX, plus pg_trgm-GIN-Index, weil pg_trgm die char-Signedness auswertet"
  - "Zone eu-central-1c für c7a bleibt Prüfpunkt in Block 14, Schritt 0: ohne Angebot beginnt die x86-Hälfte nicht, Owner entscheidet"
  - "Sweep und Kostenüberblick zählen statt zu listen, keine Kennungen in Rohdateien"
metrics:
  duration: "rund 15 min"
  completed: "2026-09-30"
  tasks: 2
  files: 2
---

# Phase 28 Plan 04: Runbook für die x86-Anfahrt und lokale Vorprobe Summary

Lokale, kostenlose Vorprobe arm64 nach amd64 (PostgreSQL 18.6 startet, amcheck und REINDEX sauber, Prüfsumme gleich; containerd-Store zieht amd64 nach) und ein Runbook, das die ganze Phase-28-Anfahrt beschreibt: Sätze je Typ, Deckel in USD je Box-Satz, x86-Box als zweite Instanz mit Machbarkeitstor, Kette mit Deckelregel und Sicherheitstimer, Abbau bis null Snapshots.

## Was gebaut wurde

- **00-vorprobe-x86.txt**: Docker Desktop 29.5.2 mit qemu, Abbildspeicher `io.containerd.snapshotter.v1` (derselbe Typ wie auf der Box, Runbook Block 8). Cluster unter `linux/arm64` mit `postgres:18.6` angelegt (UTF8, en_US.utf8, 5.000 Zeilen mit Umlauten und Zeichen über 127, B-Baum auf text und varchar, pg_trgm-GIN), sauber gestoppt, dasselbe Volume unter `linux/amd64` gestartet: Log ohne Warnung, `pg_controldata` auf beiden Seiten `signed`, Ausrichtung 8; `bt_index_check` (heapallindexed) über 167 Indizes und `gin_index_check` rc 0 vor und nach `REINDEX DATABASE` (rc 0), Index- gleich Tabellenscan (1882 und 100 Treffer), md5 über alle Zeilen gleich, Schreibzugriff danach klappt. `busybox:1.37` erst arm64, dann amd64 gezogen und gestartet, beide Varianten unter einem Tag. Ergebniszeile `vorprobe-ergebnis postgres ja abbilder ja` mit Grenzen der Aussage. Container, Volume und Abbilder entfernt und belegt.
- **runbook-messbox.md** (457 Zeilen, nur Ergänzungen):
  - 2.1 Nachtrag mit den Posten der Anfahrt, vier Posten als **NEU**.
  - 2.3 Satztabelle der sechs Typen plus Parkposten (Preiskarte, gelesen 29.09.), Hinweis auf `INSTANCE_RATES` in `aws_box.sh` (28-03) und `00-typwechsel.sh preis`.
  - 2.5 Rechenweg in USD je Box-Satz, Tabelle je Box, Summe 45,18 USD, Deckel 58,74 USD, mit Anker 59,43 USD; Stunden nur Anzeige; Vorgängerstand bleibt.
  - Block 5 und Block 12: nur m7g.large, Drop-in vor m7g.4xlarge entfernen, Matrix ohne Grenze (`GRENZE_2G=nein`, Rückleseprobe `max`).
  - Block 7b: fio über das Gerät, gefunden über die Größe, `--readonly`, dd als Rückfall.
  - Block 14: describe-images amd64, Zone und Quota per `00-typwechsel.sh quota`, zwei Zustandsverzeichnisse, `--instance-initiated-shutdown-behavior stop`, V-X per `restore`, `docker pull --platform linux/amd64`, Machbarkeitstor (PostgreSQL-Start, `occ status`, `REINDEX DATABASE`, amcheck, `files:scan`) mit Zeitdeckel 1 h 30 und Rückfällen Dump/Restore oder Harness B (C2), Vorprobe verlinkt.
  - 7.3: zehn Schritte mit Werkzeug, Rohdatei und Rückgabewerten (`02-rechenblatt.py`, `00-typwechsel.sh`, `00-kette.sh`, `10-zelle.sh`, `11-probe-route.py`, `93b-nullstand.sh`, `01-teilkorpus.py`, `12-slotkosten.py`).
  - Abschnitt 8: Reihenfolge der Phase 28, Security Group und Schlüssel erst beim zweiten Abbau, neuer Schritt 6b (`delete-snapshot`, Rücklesen `InvalidSnapshot.NotFound`, nur nach SC4 und Owner-Bestätigung C6), Sweep über 17 Regionen und beide Tagwerte, Kostenüberblick "0 Snapshots", Schritt 9 fortgeschrieben.

## Commits

| Task | Commit | Art |
|---|---|---|
| 1 | b234395a | docs: lokale Vorprobe arm64 nach amd64 |
| 2 | 9d08f30f | docs: Runbook x86, USD-Deckel, Sicherheitstimer, null Snapshots |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Erster Vorprobe-Lauf verworfen**
- **Found during:** Task 1
- **Issue:** Die Bereitschaftsprüfung meldete den arm64-Cluster während des Init-Servers bereit (zwei Abfragen scheiterten), und zwei Prüfabfragen waren nicht trennscharf (0 bzw. 5000 Treffer für jede Zeile).
- **Fix:** Warten auf "init process complete" plus Verbindung zur Datenbank, trennscharfe Abfragen auf varchar-Bereich und Trigramm; erster Lauf samt Volume und Abbildern entfernt, zweiter Lauf vollständig. In der Rohdatei vermerkt.
- **Commit:** b234395a

**2. [Rule 1 - Bug] Em-Dash aus einer Docker-Fehlermeldung**
- **Found during:** Task 1
- **Issue:** Die Meldung von `docker image rm --platform` enthält vor "-force" einen Gedankenstrich statt eines zweiten Bindestrichs.
- **Fix:** In der Rohdatei als `--force` wiedergegeben.
- **Commit:** b234395a

### Auslegung

- **Rest der Emulationsprobe:** die arm64-Variante von `alpine:3` aus Schritt 0.1 bleibt im lokalen Speicher, weil ein anderes lokales Abbild dieselbe Variante teilt; ohne `--force` belassen (kein Container, kein Volume, `alpine:3` bleibt amd64). In der Rohdatei belegt (c.4, c.5).
- **Name-Tag der x86-Instanz:** wie im Rezept von `aws_box.sh create` `findling-loadtest`, kein neuer Name.
- **Block 5/12 "nur auf m7g.large":** als datierte Nachträge in den Blöcken, der Wortlaut der Blöcke bleibt (Owner-Regel "nur erbetene Änderungen").

## Known Stubs

Keine. Die neuen Runbook-Teile tragen die Marke `in Phase 28 erstmals vollzogen`; ihr Lauf ist Teil von 28-05ff.

## Threat Flags

Keine neue Fläche: Runbook nur mit Platzhaltern (`<ami-amd64 ...>`, `<db-nutzer>`, `<datenbank>`, `<geraet>`), einzige Kennung bleibt der Korpus-Snapshot (bestehende Ausnahme); Sweeps zählen statt zu listen; Vorprobe nur lokal mit offiziellen Abbildern ohne veröffentlichten Port.

## Offene Punkte für 28-05

- Zone: c7a-Angebot in `eu-central-1c` prüfen (`00-typwechsel.sh quota c7a.xlarge c7a.2xlarge c7a.4xlarge c7a.8xlarge`), Block 14 Schritt 0. Ohne Angebot Owner-Entscheid vor der ersten Ressource.
- Auf der Box `pg_controldata` der AIO-Datenbank lesen (Signedness), weil die Vorprobe nur das Docker-Hub-Abbild prüfte.

## Self-Check: PASSED

- Dateien vorhanden: docs/runbook-messbox.md, docs/measurements/2026-10-abnahme-anfahrt/rohdaten/00-vorprobe-x86.txt
- Commits vorhanden: b234395a, 9d08f30f
- Zählungen: c7a 28, InvalidSnapshot.NotFound 1, Block 14 6, 7.3 4; genau eine Ergebniszeile in der Rohdatei; keine Em- oder En-Dashes; `git diff --stat` nur Einfügungen
- `docker ps -a`, `docker volume ls`, `docker image ls` ohne Reste der Vorprobe; Harness-Container unberührt (22 wie vorher)
- Gates: pytest test_measurement_scripts und test_public_artifacts 532 passed; keine Python-Dateien geändert
