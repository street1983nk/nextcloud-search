---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 10
subsystem: messung-str02
tags: [granite, e5, arm64, m7g, speicher, latenz, durchsatz, aws]
status: komplett
requires: [35-09]
provides:
  - "docs/measurements/2026-10-granite-vergleich/skripte/ 06, 07, 10 bis 14, 19 (narrow scope)"
  - "docs/measurements/2026-10-granite-vergleich/rohdaten/ 01, 02, 03, 06, 07, 08, 11 bis 14, 90"
affects: [35-11]
tech-stack:
  added: []
  patterns: ["Stichprobe ohne Korpus-Volllauf aus deterministischem Generator", "Text einmal im Image extrahiert, Box rechnet nur Einbettung", "Abbau mit Sitzungsprüfung und unabhängiger Gegenprobe"]
key-files:
  created:
    - docs/measurements/2026-10-granite-vergleich/skripte/06-stichprobe.py
    - docs/measurements/2026-10-granite-vergleich/skripte/07-text.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/07-text.py
    - docs/measurements/2026-10-granite-vergleich/skripte/10-box-aufbau.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/11-arm-latenz.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/12-arm-speicher.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/12-arm-speicher.py
    - docs/measurements/2026-10-granite-vergleich/skripte/13-arm-durchsatz.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/13-arm-durchsatz.py
    - docs/measurements/2026-10-granite-vergleich/skripte/14-hochrechnung.py
    - docs/measurements/2026-10-granite-vergleich/skripte/19-abbau.sh
    - docs/measurements/2026-10-granite-vergleich/rohdaten/ (12 Dateien)
  modified:
    - docs/measurements/2026-10-granite-vergleich/README.md (nur Abschnitt "Abweichungen vom Rezept (Plan 35-10)")
    - docs/measurements/2026-10-granite-vergleich/skripte/00-ablauf.md
decisions:
  - "Text der Stichprobe einmal im ausgelieferten Image (amd64) extrahiert, auf der Box nur Chunking und Einbettung"
  - "Seed phase5 nach README, obwohl der Septemberbestand mit phase5-full gebaut wurde"
  - "Deckel nur in USD, wie vom Owner abgenommen"
metrics:
  duration: "ca. 2 h 30 min (inkl. Wartezeit auf die Anmeldung); Box-Zeit 20 min 07 s"
  completed: 2026-10-20
  tasks_done: 3
  tasks_total: 3
---

# Phase 35 Plan 10: granite-Vergleich arm64 (STR-02) Summary

Auf einer nackten m7g.large (mem=4G, Container `--memory 2g`, Grenze aus der cgroup zurückgelesen) sind Latenz, RAM und Durchsatz von e5 int8 und granite int8 gemessen. Die Neu-Einbettung von 52.111 Dokumenten ist hochgerechnet. Die Box ist abgebaut, das hat 0,0362 USD gegen einen Deckel von 0,60 USD gekostet.

## Owner-Freigabe

`Owner-Freigabe: 20.10.2026, "Freigegeben (0,60 USD)"`, Deckel 0,60 USD, 5,2 h, Abbruch bei 80 Prozent (`rohdaten/02-rechenblatt-freigabe.txt`, Commit 45215015, vor jeder Ressource).

## Commits

| Task | Name | Commit |
|---|---|---|
| 1 | Box-Skripte, Stichprobe, Text, Rechenblatt | d725dc0f |
| 2 | Owner-Freigabe | 45215015 |
| 3a | arm64-Rohdaten (vor dem Abbau) | c0ade026 |
| 3b | Abbau und Schlusskosten | 43e70138 |

## Kernzahlen arm64 (m7g.large, Graviton3, Image 1.4.3 linux/arm64)

| Messgröße | e5 int8 | granite int8 |
|---|---:|---:|
| Token/s p50 (bench) | 3459,1 | 3023,3 |
| Einzelanfrage kalt p50 / max | 751,4 / 758,3 ms | 1065,3 / 1071,2 ms |
| warm p50 / p95 | 4,65 / 5,42 ms | 5,45 / 6,50 ms |
| RssAnon nach Tokenizer | 311.044 kB | 237.268 kB |
| RssAnon nach Sitzung | 443.760 kB | 304.792 kB |
| RssAnon nach erster Charge | 445.832 kB | 331.792 kB |
| memory.peak (Speicherlauf) | 716.947.456 B | 676.896.768 B |
| memory.peak (Durchsatzlauf) | 1.150.597.120 B | 618.407.936 B |
| Dokumente/min (Einbettung allein, 500 Dok.) | 195,39 | 165,68 |
| Chunks/Dokument (eigener Tokenizer, Kappe 1024) | 2,818 | 2,844 |
| Neu-Einbettung 52.111 Dok., Einbettung allein | 4 h 26 min | 5 h 14 min |
| gekoppelt, skaliert (Obergrenze nach Annahme 3) | 26 h 37 min (Bezug Sept.) | 31 h 23 min |

Die Medianwerte stammen aus 5 Starts (Latenz), 3 Läufen (Speicher) bzw. 2 Läufen (Durchsatz). Kalt bleibt bei beiden Modellen unter 1,5 s, memory.peak liegt bei beiden unter 2 GiB. Die Auswertung nach der Regel (a) bis (d) kommt in 35-11.

## Deviations from Plan

1. **[Rule 1, Bug] 19-abbau.sh hat fehlgeschlagene Gegenproben als null gezählt.**
   - **Gefunden in:** Task 3.
   - **Problem:** Die exportierten Zugangsdaten liefen nach rund 20 min ab. Der erste Abbau um 04:42Z hat nichts beendet, und das Skript meldete trotzdem "abbau belegt".
   - **Fix:** Das Skript prüft jetzt die Sitzung vor dem Abbau, und jede gescheiterte Gegenprobe beendet es rot. Zweiter Anlauf mit frischer Sitzung, Instanz beendet um 04:43:36Z. Eine unabhängige Gegenprobe über das Profil zeigt null Instanzen, Volumes, Adressen und Schlüssel.
   - **Datei:** `skripte/19-abbau.sh`.
   - **Commit:** 43e70138.
2. **Text auf dem Entwicklungsrechner extrahiert** (README-Abweichung 2). Die Box hat nur Chunking und Einbettung gerechnet. "Dokumente/min" meint deshalb Einbettung allein.
3. **Stichprobe ohne Volllauf des Korpus.** Seed `phase5` laut README, der Septemberbestand wurde mit `phase5-full` gebaut (README-Abweichung 1).
4. **Deckel nur in USD**, ohne Euro-Umrechnung (README-Abweichung 3).
5. **Anmeldung als Auth-Gate.** Die AWS-Sitzung war abgelaufen, die Arbeit lief erst nach `aws login` des Owners weiter. Das ist normaler Ablauf, kein Fehler.
6. **Kein Push, kein CI-Block.** Das übernimmt der Orchestrator.
7. **06-stichprobe.py nach dem Lauf geändert**, nur Kommentar und `noqa: S311` für das ruff-Gate. Das Verhalten ist unverändert.

## Known Stubs

Keine.

## Gates

ruff check und ruff format über `skripte/` sind grün. pyright meldet 0 Fehler auf den neuen Python-Skripten. vulture und reuse lint sind grün. `test_measurement_scripts` und `test_public_artifacts`: 622 passed. Die Rohdaten sind per Muster auf IP-Adressen und Kennungen geprüft: keine Treffer.

## Threat Flags

Keine neue Angriffsfläche. SSH war nur von der eigenen Adresse /32 offen. Die Zugangsdaten lagen nur in einer Scratch-Datei mit umask 077 und sind nach dem Abbau gelöscht. Im Repo stehen keine Kennungen.

## Self-Check: PASSED

- Rohdaten 01, 02, 03, 06, 07, 08, 11, 12, 13, 14 und 90 liegen im Repo. 12 enthält `memory.peak`.
- Die Commits d725dc0f, 45215015, c0ade026 und 43e70138 stehen im Log. Der Rohdaten-Commit c0ade026 (04:42:04Z) liegt vor dem Abbau (04:43:36Z).
- STATE.md und ROADMAP.md sind unangetastet. Kein Push.
