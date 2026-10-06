---
phase: 28-abnahme-anfahrt
plan: 07
subsystem: messung
tags: [abnahme-anfahrt, teilkorpus, m7g.large, m7g.4xlarge, arm-baseline, zaehltor, mess-10]
requires:
  - phase: 28-06
    provides: Referenzbox m7g.large mit S-voll und C1, Box geparkt, Deckel 59,43 USD
provides:
  - "Teilkorpus-Liste teilkorpus-liste.txt (5.000 Zeilen name,bytes,sha256 plus listen-pruefsumme f6b3dd70...)"
  - "04-teilkorpus-arm.txt: Inventar, 19 Ordner-Ausschlüsse, Zähltor 5000, Protokoll der Läufe 1 bis 6 auf m7g.large"
  - "Rohdaten Zelle 2 S-T-anker (m7g.large) und Zellen 5 S-T, 6 St-T, 7 L-T (m7g.4xlarge)"
  - "05-typwechsel-arm.txt: mem=4G entfernt, Rücklesung 61Gi/16/aarch64, memory.max max je Zelle, Läufe 7 bis 9"
  - "Kettenwerkzeug im Feld gehärtet (Zähltor, Vorrats-Tor, Restart, Abbruchcodes 73/74) über sechs Quick-Tasks und ein Debug"
  - "Kostenstempel 90-kosten.txt bis Lauf 9: bisher 12,69 USD gegen Deckel 59,43 USD, ARM-Box geparkt"
affects: [28-08, 28-09, 28-10, 28-11]
tech-stack:
  added: []
  patterns:
    - "Zähltor teilkorpus-scharf: Zählmarke vor dem Trigger, frische Zustände nur unter files/teilkorpus, Vorrat pfadscharf aus oc_findling_queue"
    - "Vorrats-Tor vor der Bewaffnung (Abbruch 73 beziffert Altbestand), occ findling:index --restart räumt den Arbeitsvorrat"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/teilkorpus-liste.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/04-teilkorpus-arm.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/05-typwechsel-arm.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.large/S-T-anker/
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.4xlarge/S-T/
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.4xlarge/St-T/
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/m7g.4xlarge/L-T/
  modified:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/90-kosten.txt
decisions:
  - "Owner 03.10. (Quick 261003-d3y, D-24-07 P2): Probe prüft die Vorschlags-Schwellen, Zellen 3, 4 (St-T/L-T m7g.large) und 10 (L-T c7a.xlarge) gestrichen, Matrix damit 18 Zellen"
  - "Owner 03.10. (Quick 261003-wxg, a + b): Reconcile beachtet die Ausschlüsse (Produkt-Fix), Zähltor-Vorrat pfadscharf (Werkzeug)"
  - "Owner nach Lauf 8: Produkt-Fix vor Harness-Patch, Debug crawl-unfinished-zweitlauf (Reconcile steht still, solange der Crawl läuft), dann Lauf 9"
metrics:
  duration: "01.10. bis 04.10.2026 (Teilkorpus 01.10., Zelle 2 am 02.10., Zellen 5 und 6 am 03.10., Zelle 7 Lauf 9 am 04.10. 04:32Z bis 06:15Z)"
  completed: 2026-10-04
requirements: [MESS-10]
---

# Phase 28 Plan 07: Teilkorpus und ARM-Hälfte der Matrix Summary

**Rückwirkender Close-out vom 05.10.2026:** Der Plan wurde über mehrere Sessions vollständig ausgeführt, das SUMMARY wurde erst nach Abschluss der gesamten Matrix aus Rohdaten, STATE.md und den `docs(28-07)`-Commits geschrieben; es wurde dafür nichts neu gemessen.

Teilkorpus mit exakt 5.000 Dateien auf der ARM-Platte eingerichtet (Liste mit Prüfsumme committet), Anker S-T auf m7g.large und die ARM-Baseline S-T, St-T, L-T auf m7g.4xlarge gemessen (alle rc 0, Zähltor je 5000, alle drei m7g.4xlarge-Zellen von der Rechnung getragen). Der Weg dahin brauchte neun Kettenläufe, sechs Quick-Tasks und ein Debug, die das Kettenwerkzeug und zwei Produktstellen im Feld gehärtet haben. Die ARM-Box ist geparkt, Stand 12,69 von 59,43 USD.

## Hinweis zum Commit-Label

Der Executor hat das Label `docs(28-07)` auch für die gesamte x86-Hälfte weitergeführt (Commits 147a6ed8 bis 6022063c). Inhaltlich gehören diese Commits zu 28-08 (c7a.xlarge) und 28-09 (c7a.2xlarge bis c7a.8xlarge) und sind dort zugeordnet.

## Task-Stand

### Task 1: Teilkorpus einrichten und die Teilkorpus-Zellen auf m7g.large

- **Teilkorpus:** Hardlinks per `01-teilkorpus.py hardlinks` nach `lasttest/files/teilkorpus`, `occ files:scan`, 19 Ordner-Ausschlüsse für alle übrigen Top-Level-Ordner der Homes, Liste von der Box geholt. `teilkorpus-liste.txt`: 5.000 Datenzeilen plus `listen-pruefsumme f6b3dd70971035374d502dfd27ac0dc8dd372f033c9fc4e12aa462e887c09979` (Commit 4d30864c).
- **Zelle 2 S-T-anker GEMESSEN (Lauf 6, 02.10.):** Vorrats-Tor altvorrat 0, Grenze 2147483648/0, Baumhash-Beweis ja, Wirksamkeit economy slotsInForce 1, Zähltor bestanden 5000 (08:56:55Z, erster Feldbeweis der Frischzählung aus 261002-cvf), Zelle-Ende rc 0 um 11:46:29Z, Dauer 3:50 wie geplant (Commits e268175a, 06545083). Rohdaten `m7g.large/S-T-anker/`.
- **Zellen 3 St-T und 4 L-T auf m7g.large: GESTRICHEN.** Lauf 6 brach St-T mit 69 ab: Probe sagt fits, `profile.effective()` deckelt aber auf `suggest()` (Standard verlangt >= 6 GB und >= 3 Kerne), wirksam blieb economy. Owner-Entscheid 03.10. (Quick 261003-d3y, P2): die Probe prüft die Vorschlags-Schwellen vor der Messung (nofit hardware_short), die Zellen 3, 4 und 10 entfallen. Rohdaten der Abbruchzelle unter `m7g.large/St-T-abbruch69-lauf6/`.

### Task 2: Typwechsel auf m7g.4xlarge und die ARM-Baseline

- **Typwechsel (Lauf 7, 03.10.):** `mem=4G` entfernt 11:13:39Z (`grep -c mem=4G /boot/grub/grub.cfg` = 0), `typwechsel m7g.large -> m7g.4xlarge` gestoppt 11:14:27Z, läuft 11:14:49Z; Rücklesung 61Gi, nproc 16, aarch64, `mem=4G` nicht in /proc/cmdline. `memory.max max` je Zelle protokolliert (D-28-12).
- **Zelle 5 S-T GEMESSEN:** rc 0, Zähltor 5000, 3:39 h, anon-max 1.499,6 MiB gegen Grenze 1.641,8, getragen (de6e14ac).
- **Zelle 6 St-T GEMESSEN:** Probe fits (Reserve 62,1 GB, 4 Slots), wirksam standard/4, Zähltor 5000, anon-max 2.358,2 MiB gegen 2.528,8, getragen (2dad3cd4).
- **Zelle 7 L-T GEMESSEN erst in Lauf 9 (04.10.):** Probe fits (15 Slots), erzwungen nein, wirksam performance, Wächter ohne Absenkung, OOM 0, Zähltor 5000, anon-max 5.481,8 MiB gegen Rechnung 5.033,0 und Grenze 5.536,3, getragen (21721984). Slot-anon je Slot 220,1 MiB (B2 235), Hauptprozess-Maximum 2.319,0 MiB.
- **Stopp:** Kette setzte `shutdown -h +2` vor dem Abholen; kurzer Abholstart, `aws_box.sh stop` 06:15:06Z, BOX_STOPPED_ISO gesetzt, ARM-Box geparkt. Kosten 12,69 von 59,43 USD (f36f704b).

## Abweichungen vom Plan

### Gestrichene Zellen

- Zellen 3 und 4 (m7g.large St-T/L-T) per Owner-Entscheid 03.10. gestrichen, ebenso Zelle 10 (c7a.xlarge L-T). Der Plan erwartete sechs Zellen, gemessen sind vier. Die Matrix zählt damit 18 Zellen (einschließlich S-voll aus 28-06).

### Kettenabbrüche und daraus entstandene Fixes (in Reihenfolge)

1. **Läufe 1 bis 3, Abbruch 71 am Zähltor:** Zählformel zählte indexiert statt eingebettet, dazu eine Leserace. Quick 261001-vl0 (6d114659, Tests e23cd72b).
2. **Lauf 4, beidseitig 73 am Vorrats-Tor:** Top-up-Route schob Altvorrat nach. Quick 261002-93i (`occ findling:index --restart` räumt den Arbeitsvorrat, Produkt-Fix 09e641ef; 93b urteilt über den Vorrat), danach Quick 261002-af9 (Vorrats-Tor vor die Bewaffnung gezogen).
3. **Lauf 5, Abbruch 71 mit 5041:** 41 Alt-Endzustände außerhalb des Teilkorpus in `oc_findling_file_state` zählten mit. Quick 261002-cvf (Zähltor pfadscharf mit Zählmarke).
4. **Lauf 6, Abbruch 69 bei St-T:** Wirksamkeit gedeckelt, siehe oben, Quick 261003-d3y.
5. **Lauf 7, L-T zweimal Abbruch 71 mit 5549:** Reconcile plante 549 ausgeschlossene Dateien in jeder ruhigen Runde neu ein (Produktbefund mit Nutzerrelevanz). Quick 261003-wxg: Reconcile beachtet die Ausschlüsse (6dd65fc3), Zähltor-Vorrat pfadscharf (12c659dd).
6. **Lauf 8, L-T Abbruch 71 mit 5427:** zweiter Crawl-Durchgang über den fertigen Teilkorpus nach dem Selbstvorschub. Debug crawl-unfinished-zweitlauf: Queue-Statistik meldet den unfertigen Crawl (13993fd9), Reconcile steht still, solange der Crawl unfertig ist (01b1afce), aufgelöst in 18602c48. Lauf 9 auf Abbild 5ed5742c (Multi-Arch zu 18602c48) bestätigte den Fix im Feld (keine stale-Lieferung, ruhige Runde stale=0, unchanged 0).

Jede Werkzeugänderung lief mit Owner-Wort (Runbook 7.1). Abbild und Code-Stand der Box wanderten dadurch von c87a0239 über bbd23578 auf 18602c48; Baumhash je Lauf belegt.

### Umgebung und Betrieb

- **AWS-Sitzung abgelaufen (Auth-Gate, Läufe 5 und 8):** `aws_box.sh stop` scheiterte, die Box wurde von innen gestoppt (Shutdown-Verhalten stop belegt), die AWS-Bestätigung per `aws_box.sh status` wurde nach dem Owner-Login nachgeholt (Lauf-8-Stopp bestätigt 04.10. 04:31Z).
- **Platzhalter-Gate:** 05-typwechsel-arm.txt und STATE.md trugen zwei Box-Adressen aus Lauf 8/9, ersetzt durch den Legende-Platzhalter in 147a6ed8. Die alten Werte stehen weiterhin in der lokalen Historie (Push-Entscheid offen).
- **`STOPP_AM_ENDE=nein` wird von `00-kette.sh` nicht gelesen** (Befund schon aus 28-06): jede Kette endet mit Stopp, jeder weitere Lauf brauchte Start und Bewaffnung.

## Offene Produktbefunde (nicht angefasst)

- **Embed-Übergabe-Timeout (Lauf 9):** zweimal "could not move 30 files to the embed track, they run into the lock timeout" (05:02:56Z, 05:34:19Z). Die Dateien hängen bis zum OCR-Lock-Ablauf (1.800 s) und werden einmal neu OCR-verarbeitet. Nutzerrelevanz: bis 30 min verzögerte Vollständigkeit, doppelte OCR, kein Datenverlust. Kandidat /gsd-debug, Owner.

## Known Stubs

Keine (reine Mess- und Protokollartefakte).

## Self-Check: PASSED

- teilkorpus-liste.txt: 5.002 Zeilen (Kopf, 5.000 Daten, Prüfsumme), FOUND
- rohdaten/m7g.large/S-T-anker/, m7g.4xlarge/S-T, St-T, L-T, 04-teilkorpus-arm.txt, 05-typwechsel-arm.txt: FOUND
- Commits 4d30864c, e268175a, 06545083, de6e14ac, 2dad3cd4, 21721984, f36f704b: FOUND
