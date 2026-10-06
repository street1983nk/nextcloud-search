---
phase: 28-abnahme-anfahrt
plan: 08
subsystem: messung
tags: [abnahme-anfahrt, x86, c7a.xlarge, machbarkeitstor, fp32, mess-10]
requires:
  - phase: 28-07
    provides: ARM-Hälfte gemessen, Teilkorpus-Liste mit Prüfsumme, ARM-Box geparkt, Code-Stand 18602c48
provides:
  - "06-aufbau-x86.txt: x86-Box c7a.xlarge (Runbook Block 14), Machbarkeitstor bestanden in 45 min, Baumhash, Cron-Gate, vorpruefung-stop-ja, Teilkorpus mit gleicher Listen-Prüfsumme"
  - "Rohdaten Zellen 8 S-T, 9 St-T, 11 St-fp32-T auf c7a.xlarge inklusive fp32-Live-Download und Rückkehr auf int8"
  - "Erster fp32-Datenpunkt: Mehrbedarf 509,7 MiB gegen FP32_EXTRA_BYTES 367 MiB, Zelle 11 nicht getragen (SC4/C5)"
  - "Kostenstempel c7a.xlarge 8,6594 h = 2,1848 USD"
affects: [28-09, 28-10, 28-11]
tech-stack:
  added: []
  patterns:
    - "x86-Umzug des Snapshot-Stacks: Abbilder je Index-Digest des Snapshot-Stands ziehen, Container einzeln neu erzeugen, amcheck vor und nach REINDEX"
    - "Lesender Helfer am Kettenende: shutdown +2 durch Sicherheitsstopp +60 ersetzen und den Abwärtsweg auf int8 fahren"
key-files:
  created:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/06-aufbau-x86.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/07-typwechsel-x86.txt
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.xlarge/
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/c7a.xlarge-kette.log
  modified:
    - docs/measurements/2026-10-abnahme-anfahrt/rohdaten/90-kosten.txt
decisions:
  - "Owner-Tor Task 1: Weg x86-tor (Snapshot-Stack mit Machbarkeitstor auf der Box), Owner-Wort vom 04.10.2026"
  - "Zelle 10 (L-T c7a.xlarge) bleibt gestrichen (Owner 03.10., Quick 261003-d3y)"
  - "Box läuft auf Abbild 5ed5742c (Multi-Arch zu 18602c48) statt auf dem c87a0239-Stand, gleicher Stand wie ARM-Lauf 9"
metrics:
  duration: "04.10.2026 06:24:49Z bis 15:04:23Z (8,66 h Boxzeit, davon Tor 45 min, Kette 07:15:46Z bis 15:03:23Z)"
  completed: 2026-10-04
requirements: [MESS-10]
---

# Phase 28 Plan 08: x86-Einstieg mit Machbarkeitstor und c7a.xlarge inklusive fp32 Summary

**Rückwirkender Close-out vom 05.10.2026:** Der Plan wurde am 04.10. vollständig ausgeführt, das SUMMARY wurde erst nach Abschluss der gesamten Matrix aus 06-aufbau-x86.txt, 07-typwechsel-x86.txt, 90-kosten.txt, STATE.md und den Commits geschrieben; es wurde dafür nichts neu gemessen.

Der Owner wählte den Weg x86-tor. Die zweite Instanz c7a.xlarge wurde aus demselben Snapshot aufgebaut, das Machbarkeitstor bestand in 45 min (PostgreSQL 18.6 auf x86_64, amcheck vor und nach REINDEX sauber). Auf c7a.xlarge sind S-T, St-T und St-fp32-T gemessen (alle rc 0, Zähltor je 5000); die fp32-Datei kam live aus dem eigenen Release. Zelle 11 St-fp32-T wird von der Rechnung nicht getragen (fp32-Mehrbedarf 509,7 statt 367 MiB), das geht als SC4/C5-Fall an den Owner.

## Task-Stand

### Task 1: Owner-Tor vor der ersten x86-Box (checkpoint:decision)

- **Signal:** in einer früheren Session gegeben. Der Wortlaut des Owners selbst ist nicht überliefert. Überliefert ist die Übermittlung durch den Orchestrator, festgehalten im Kopf von `06-aufbau-x86.txt`: "eigener x86-boxaufbau (c7a), machbarkeitstor auf c7a.xlarge zuerst, dann die zellen der matrix", Weg **x86-tor**, Owner-Wort vom 04.10.2026.
- **Vollzug belegt:** Vor dem Signal gab es keine x86-Ressource. Schritt 0 (Abbildsuche, Quota 32 vCPU, Angebot aller vier c7a-Typen in eu-central-1c, ARM-Box `stopped`, Deckel bisher 12,69 USD) lief kostenlos vor `run-instances`, LaunchTime 06:24:49Z.

### Task 2: x86-Aufbau und Machbarkeitstor auf c7a.xlarge

- **Instanz:** c7a.xlarge, x86_64, eu-central-1c, gemeinsame Security Group und gemeinsames Schlüsselpaar, `--instance-initiated-shutdown-behavior stop`, eigenes Zustandsverzeichnis x86, Volume aus dem Korpus-Snapshot.
- **Tor:** Abbilder nicht per Tag, sondern je Index-Digest des Snapshot-Stands gezogen, AIO-Container einzeln neu erzeugt (alle `uname -m x86_64`). PostgreSQL 18.6 auf x86_64 gestartet, amcheck 656 B-Bäume vor und nach `REINDEX DATABASE` rc 0, `occ status` (maintenance false, needsDbUpgrade false), `files:scan` einer Stichprobe. Ergebniszeile: `tor-ergebnis bestanden dauer 45 min (06:26:46Z bis 07:12:02Z, zeitdeckel 90 min)`.
- **Nach dem Tor:** Abbild `sha256:5ed5742c...` (Multi-Arch zu 18602c48), Baumhash im laufenden Container `ee918ce4...` gleich ARM-Lauf 9, `baumhash-beweis ja`; Cron-Gate erfüllt (Cron-Intervall 300 s, AIO-Cron-Container); `vorpruefung-stop-ja 2026-10-04T07:15:44Z`.
- **Teilkorpus:** Hardlinks 5.000 (Linkzahl 2), `files:scan` Files 5000 Errors 0, dieselben 19 Ordner-Ausschlüsse wie auf ARM, `listen-pruefsumme f6b3dd70...` über loadtest und teilkorpus gleich, Datei byte-gleich mit `teilkorpus-liste.txt`, `listen-pruefsumme-gleich ja`.
- Commit 147a6ed8.

### Task 3: Zellen auf c7a.xlarge einschließlich fp32

Laufwerte: ZELLEN S-T, St-T, St-fp32-T (Zelle 10 L-T gestrichen), GRENZE_2G nein, SATZ_USD_H 0.252301, KORPUS_FRIST 3600. Kette 07:15:46Z bis 15:03:23Z, alle drei Zellen rc 0.

| Zelle | Profil | Probe | Zähltor | anon-max MiB | Grenze MiB | Urteil |
|-------|--------|-------|---------|--------------|------------|--------|
| 8 S-T | economy/int8, 1 Slot | keine (Abwärtsweg) | 5000 | 1.520,2 | 1.641,8 | getragen |
| 9 St-T | standard/int8, 1 Slot | fits, erzwungen nein | 5000 | 1.679,5 | 1.753,3 | getragen |
| 11 St-fp32-T | standard/fp32, 1 Slot | fits, erzwungen nein | 5000 | 2.172,5 | 2.157,0 | **nicht getragen** |

- **fp32-Probe (Zelle 11):** Nullstand vor der Probe, Download live aus dem Release model-e5-small-fp32-614241f, Fortschritt 47.185.920 bis 470.268.510 von 470.268.510 Bytes in rund 18 s. Digest: das Produkt prüft Länge und sha256 (`embed/weights.py`), die WRONG_DIGEST-Warnung fehlt im Log, die Probe ging in den Schritt model, die Übersicht meldet `storedPrecision=fp32`.
- **fp32-Mehrbedarf:** Hauptprozess int8 1.430.464 kB, fp32 1.952.360 kB, Mehrbedarf 509,7 MiB gegen FP32_EXTRA_BYTES 367 MiB. Die Probe stimmt (fits, kein Wächtereingriff, kein OOM, Spitze 3,1 GB auf 7,6 GiB); der Widerspruch liegt bei der Rechnung, nicht beim Verdikt.
- **Rückkehr auf int8 belegt** (`99-rueckkehr-int8.txt`): Abwärtsweg `code=saved` HTTP 200, danach `storedPrecision=int8 profileSaved=economy` (15:03:27Z bis 15:03:30Z).
- **Gegenprobe aller Zellen:** kein Wächtereingriff, OOM 0, restartcount 0. Crawl-Fix aus 28-07 auf x86 bestätigt (nur "crawl is unfinished" während des Crawls, keine stale-Lieferung, ruhige Runde stale=0, unchanged 0).
- **Stopp und Kosten:** Stopp im Typwechsel auf c7a.2xlarge 15:04:23Z, Laufzeit 8,6594 h x 0,252301 = 2,1848 USD, bisher 14,87 USD nach der Kette. Die Box blieb nicht geparkt, sondern wurde direkt per Typwechsel für 28-09 weiterverwendet (geplanter Ablauf, gleiche Instanz).
- Commits cd737a12, 1e1cb157, 65ac107a, 5e536753, 4a45f184.

## Abweichungen vom Plan

1. **Abbild-Stand:** Der Plan nennt den Multi-Arch-Digest zu c87a0239. Gemessen wurde auf 5ed5742c (Multi-Arch zu 18602c48), weil die Fixe aus 28-07 (Reconcile, Crawl) im Abbild sein mussten. Gleicher Stand wie ARM-Lauf 9, Baumhash belegt.
2. **Abbilder per Index-Digest statt `docker pull --platform linux/amd64 <abbild>:<tag>`:** genauer, weil so exakt der Snapshot-Stand gezogen wird.
3. **Drei statt vier Zellen:** Zelle 10 L-T per Owner-Entscheid vom 03.10. gestrichen.
4. **Zelle 11 nicht getragen:** offener SC4/C5-Entscheid beim Owner, gehört zu 28-11, hier nicht entschieden.
5. **Satz c7a.xlarge:** Die Rückleseprobe von `aws_box.sh status` nannte 0,234260 USD/h, Kette und Kostenzeile rechnen mit dem Plansatz 0,252301 USD/h (höher, also zum Deckel hin vorsichtig). Nicht nachgeprüft, welcher Satz der Tabelle in `aws_box.sh` aktuell ist.

## Beobachtungen

- Lock-Timeout einmal in Zelle 11: "could not move 2 files to the embed track, they run into the lock timeout" (12:59:23Z), gutartig, Zähltor und Ende nicht berührt. Gleiche Familie wie der Lauf-9-Befund aus 28-07 und der Befund nach der Rückkehr fp32 auf int8 in 28-09.
- Slot-anon je Slot bei 1 Slot auf x86 rund 296 MiB (B2 235 MiB), Hauptprozess-Maximum S-T 1.288,5, St-T 1.396,9, St-fp32-T 1.906,6 MiB.
- Der Containerlog von S-T ging mit dem Nullstand von St-T verloren; ab St-T schneidet ein lesender Mitschnitt jeden Container mit.

## Known Stubs

Keine (reine Mess- und Protokollartefakte).

## Self-Check: PASSED

- 06-aufbau-x86.txt mit `tor-ergebnis bestanden dauer 45 min`: FOUND
- rohdaten/c7a.xlarge/S-T, St-T, St-fp32-T (mit 11-probe.txt und 99-rueckkehr-int8.txt): FOUND
- Commits 147a6ed8, cd737a12, 1e1cb157, 65ac107a, 5e536753, 4a45f184: FOUND
