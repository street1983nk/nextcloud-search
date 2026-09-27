---
phase: 22-messanfahrt-bl-f03
plan: 06
subsystem: messwerkzeuge
tags: [generalprobe, ci, w4, f4, b7, 92d, harp, push, v13]
requires:
  - "22-01 (W4-Job slots in measure.yml mit F4-Definition)"
  - "22-02 bis 22-05 (Box-Werkzeuge, Ablauf, Erwartungen, README-Gerüst)"
provides:
  - "Generalprobe aller Box-Werkzeuge (README Abschnitt 3), vier Befunde behoben"
  - "W4-Vorabkurve aus dem arm64-Runner: F4 3,955, D-03 angewandt (B4 gefahren), B7 22,99 MB"
  - "Box-Digest-Kandidat sha256:40ca8c2b9786151640665c378a522f200905ae428d8bbcadebdc2097c7925e3e, Abbildstrecke Lauf 174"
  - ".github/workflows/probe-92d.yml: 92d Phase B im arm64-Runner (nur workflow_dispatch), grün ab v1.1.0"
affects:
  - "22-07 (Rechenblatt: B4_GEPLANT=ja, B4 als eigener Deckelposten; Box-Digest-Kandidat)"
  - "22-08 (Anfahrt: 92d ist in Phase B einmal gefahren, occ upgrade 0 und 3 gelten)"
  - "Phase 23 (Versionssprung 1.3.0 in beiden info.xml steht noch aus)"
tech-stack:
  added: []
  patterns:
    - "Box-Werkzeug-Probe im CI mit Container-Nextcloud statt Composite-Action, weil das Werkzeug docker exec und docker cp in /var/www/html fährt und Nextclouds am Abbildnamen zählt"
    - "Probe startet ab dem Release, das dem Box-Snapshot entspricht (from_tag), und warnt, wenn Start und Ziel gleich sind"
key-files:
  created:
    - .github/workflows/probe-92d.yml
    - docs/measurements/2026-09-v13-messung/rohdaten/w4-ci-arm64/ (12 Dateien, Artefakt w4-arm64 unverändert)
    - .planning/phases/22-messanfahrt-bl-f03/22-06-SUMMARY.md
  modified:
    - docs/measurements/2026-09-v13-messung/skripte/92d-wechsel.sh
    - docs/measurements/2026-09-v13-messung/skripte/91m-langsame-aufrufe.py
    - docs/measurements/2026-09-v13-messung/skripte/94c-bodensatz-zyklen.sh
    - docs/measurements/2026-09-v13-messung/skripte/00-abholen.sh
    - docs/measurements/2026-09-v13-messung/README.md
    - backend/tests/test_v13_wechsel.py
    - .planning/phases/22-messanfahrt-bl-f03/deferred-items.md
    - .planning/phases/22-messanfahrt-bl-f03/22-06-PLAN.md
decisions:
  - "D-03 angewandt: F4 = 3,955 >= 1,5, B4 wird gefahren (B4_GEPLANT=ja); K1 nicht ausgelöst"
  - "Box-Digest-Kandidat ist sha256:40ca8c2b...3e3e (docker.yml Lauf 174, Commit 59f05fe); spätere Pushes ohne Änderung in backend/src entwerten ihn nicht, Beweis bleibt der Baumhash"
  - "92d nimmt von occ upgrade 0 und 3 (ERROR_UP_TO_DATE) als gelungen an"
  - "92d Phase B ist im CI geprobt (Owner-Option B vom 26.09.); probe-92d.yml bleibt dispatch-only und startet standardmäßig ab v1.1.0, dem Stand des Snapshots"
metrics:
  duration: "ca. 35 min (Task 3 und Zusatzprobe, ohne Task 1)"
  completed: 2026-09-26
  tasks: 3
  files: 22
---

# Phase 22 Plan 06: Generalprobe, Push, W4 und 92d-Probe Summary

Jedes Box-Werkzeug ist vor der bezahlten Zeit einmal gelaufen, 92d Phase B eingeschlossen, die im CI-arm64-Runner gegen eine frische Nextcloud mit HaRP geprobt wurde. W4 lief im kostenlosen arm64-Runner: F4 = 3,955, also wird B4 nach D-03 gefahren. B7 (niederländischer Automat, nativ arm64) steht mit 22,99 MB, und der Box-Digest-Kandidat ist per Lauf der Abbildstrecke belegt.

## Aufgaben

| Task | Name | Commits | Dateien |
| ---- | ---- | ------- | ------- |
| 1 | Generalprobe lokal, Befunde beheben | 463fcfe, a65c9c5, 5d97688, c24f142, 399ff7e, 59f05fe | 91m, 94c, 00-abholen, Tests, README Abschnitt 3 |
| 2 | Owner-Freigabe Push | (Checkpoint) | Owner "weiter" am 26.09.2026, im Plan unter `<result>` festgehalten |
| 3 | Push, W4-Lauf, F4 und B7 | c1c934b | rohdaten/w4-ci-arm64/ (12 Dateien), README Abschnitt 2 |
| Zusatz (Owner-Option B) | 92d Phase B im CI | bbf929e, f43f9e8, 2745b2c, aa8b615 | 92d-wechsel.sh, test_v13_wechsel.py, probe-92d.yml, README, deferred-items, Plan |

## Push und CI

- Push 61255f3..59f05fe (26 Commits, ohne force), danach 59f05fe..c1c934b und c1c934b..2745b2c, alle unter derselben Freigabe.
- Läufe zu 59f05fe alle grün: Multi-arch image 174 (36215893830), Python gates, Integration, Resilience, HaRP deploy (36215893831). Zu c1c934b ebenfalls alle fünf grün (HaRP deploy 36216793713).
- Digest per `docker buildx imagetools inspect ...:dev`: `sha256:40ca8c2b9786151640665c378a522f200905ae428d8bbcadebdc2097c7925e3e`, gepusht vom Merge-Job von Lauf 174 auf `:dev` und auf den Commit-Tag.

## W4 (measure.yml Lauf 4, 36216002856, alle drei Jobs grün)

- Maschine: ubuntu-24.04-arm, 4 CPUs, Neoverse-N2.
- W3 Seiten je Sekunde (Median): N 1 0,288, N 2 0,575, N 4 1,139; Faktoren 1,997 und 3,955; keine Runde mit verlorenem Slot, Speicherzuwachs je Slot unter einem MB.
- Einzelmodus: OMP_THREAD_LIMIT=1 3,470 s, ungesetzt 2,485 s bei rund 2,3 Kernen CPU.
- Einbettung T 1/2/4: 1836,9 / 3638,5 / 7109,0 Tokens je Sekunde (p50).
- B7: 22,99 MB in drei Läufen (produktnah amd64 24,2 bis 25,3, Research 17,6); Kennzahlen exakt wie erwartet.
- `F4 3.955`; D-03 angewandt, B4 gefahren; K1 nicht ausgelöst.

## 92d Phase B im CI (probe-92d.yml)

- Lauf 2 (36217297257, ab v1.1.0): `occ upgrade` fuhr das App-Update 1.1.0 auf 1.2.0 mit 0; unregister ohne `--rm-data` 0; Volumen `nc_app_findling_backend_data` bleibt mit gleicher Erstellungszeit; Registrierung ja; Grenze 2147483648/0; Baumhash im laufenden Container gleich; Bestandstor 26 / 7 / 6 bestanden; danach dieselben Zahlen aus `index_status` und ein Suchtreffer; 92d endet mit `92D-WECHSEL-FERTIG`.
- Gegenprobe im selben Lauf: Bestand um eins daneben, 92d endet mit 41, Bestand unverändert.
- Lauf 1 (36216798070, ab v1.2.0) war ebenfalls grün, hatte aber kein App-Update ("No upgrade required."), weil der Baum noch 1.2.0 trägt. Deshalb die Umstellung auf v1.1.0.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 92d wies occ upgrade mit Rückgabe 3 als gescheitert ab**
- **Gefunden bei:** Bau der CI-Probe (deploy-harp.yml, "Store upgrade 4", belegt 3 = ERROR_UP_TO_DATE als legitime Antwort)
- **Problem:** 92d verlangte 0 allein; eine Nextcloud, die "nichts zu tun" mit 3 meldet, hätte die Anfahrt mit 40 beendet.
- **Fix:** 0 und 3 gelten als gelungen, 3 schreibt zusätzlich `occ-upgrade-stand aktuell`; Wächter `test_the_image_switch_counts_up_to_date_as_a_successful_upgrade`.
- **Einschränkung:** Die Probe selbst sah auf Nextcloud 34 für "No upgrade required." eine 0, die 3 ist also nur über deploy-harp.yml belegt. Die Commit-Nachricht von bbf929e sagt zu stark, ein zweiter Lauf hätte mit 40 geendet; der 92d-Kommentar ist in 2745b2c richtiggestellt.
- **Dateien:** 92d-wechsel.sh, backend/tests/test_v13_wechsel.py
- **Commits:** bbf929e, 2745b2c

**2. [Rule 1 - Bug] Die erste Fassung der Probe prüfte das App-Update nur scheinbar**
- **Gefunden bei:** Auswertung von Lauf 1
- **Problem:** Start ab v1.2.0, Ziel ist der Baum mit 1.2.0; die Prüfung "installiert gleich Baum" war trivial wahr.
- **Fix:** Eingabe `from_tag` mit Vorgabe v1.1.0 (Stand des Snapshots), Warnung, wenn Start und Ziel gleich sind.
- **Commit:** 2745b2c

### Owner-gewählte Zusatzarbeit

**3. 92d Phase B als eigener CI-Lauf (Owner-Option B, 26.09.2026)** mit neuem Workflow `probe-92d.yml`: nur workflow_dispatch, bremst keinen Push, gleiche Action-Pins wie die übrigen Workflows (test_workflow_pins grün).

## Known Stubs

Keine. README Abschnitte 1, 4, 5 und 6 sind planmäßig offen (22-07 und nach der Anfahrt).

## Threat Flags

| Flag | Datei | Beschreibung |
|------|-------|--------------|
| threat_flag: ci-surface | .github/workflows/probe-92d.yml | neuer Dispatch-Workflow mit Docker-Socket für HaRP und `--net host`; nur read-Token, Wegwerf-Runner, Eingaben per Muster geprüft, Testpasswort ohne Wert außerhalb des Runners |

## Offene Punkte

- Versionssprung auf 1.3.0 in beiden info.xml steht noch aus (Phase 23); auf der Box installiert 92d die PHP-Hälfte daher als 1.2.0 (deferred-items.md).
- MESS-07 wird hier nicht als erledigt markiert; das Messergebnis liefert erst die Anfahrt.

## Self-Check: PASSED

- f4.txt, README (D-03-Zeile, Box-Digest-Kandidat, Laufnummer), probe-92d.yml und alle 12 Rohdateien vorhanden
- Commits 463fcfe, a65c9c5, 5d97688, c24f142, 399ff7e, 59f05fe, bbf929e, f43f9e8, c1c934b, 2745b2c, aa8b615 in der Historie
