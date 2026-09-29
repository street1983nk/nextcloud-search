---
phase: 26-n-ocr-slots-und-speicherw-chter
plan: 13
subsystem: ops-measurement
tags: [nice, latency, issue-19, D-26-12]
status: complete
requires: ["26-01 (nice 10 im Kind)", "26-09", "26-10"]
provides: ["scripts/ops/latency_probe.py", "docs/measurements/2026-09-nice-latenz/"]
affects: ["Issue-#19-Antwort (nur nach Owner-Freigabe)"]
tech-stack:
  added: []
  patterns: ["A/B über zwei Abbilder statt Testschalter im Produkt", "getrennte Reihen je cgroup"]
key-files:
  created:
    - scripts/ops/latency_probe.py
    - backend/tests/test_latency_probe.py
    - docs/measurements/2026-09-nice-latenz/README.md
    - docs/measurements/2026-09-nice-latenz/raw/A-search.txt
    - docs/measurements/2026-09-nice-latenz/raw/A-status.txt
    - docs/measurements/2026-09-nice-latenz/raw/B-search.txt
    - docs/measurements/2026-09-nice-latenz/raw/B-status.txt
    - docs/measurements/2026-09-nice-latenz/raw/machine.txt
    - docs/measurements/2026-09-nice-latenz/raw/images.txt
  modified: []
decisions:
  - "ExApp-Container im Messaufbau auf 1 CPU begrenzt (docker update --cpus 1), sonst konkurriert ein OCR-Slot auf 12 vCPU mit nichts"
  - "Harness = scripts/dev/compose-harp.yaml (NC 34.0.3); die nc35-Container gehören dem Connector-Projekt und blieben unberührt"
  - "Registry auf 127.0.0.1:5055 statt 5000 (5000 belegt durch nc-mcp-exapp-registry)"
metrics:
  completed: 2026-09-29
  tasks: "3/3"
---

# Phase 26 Plan 13: Live-Latenzprobe nice 10 Summary

Inhaltsfreie Latenzprobe mit getrennten Reihen für die Findling-Suche und status.php; A/B-Messung (Abbild c6868c21 nice 0 gegen 46572f4d nice 10) unter laufender OCR in Sparsam: kein belegbarer Unterschied bei p50/p95, weder für die Suche noch für status.php.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 (RED) | Tests für latency_probe | fb124643 | backend/tests/test_latency_probe.py |
| 1 (GREEN) | latency_probe.py | 5f754064 | scripts/ops/latency_probe.py, backend/tests/test_latency_probe.py |
| 2 | Live-Probe A/B, Rohdaten, README | b3daaa33 | docs/measurements/2026-09-nice-latenz/ |
| 3 | Owner-Abnahme | siehe Abschlusscommit | docs/measurements/2026-09-nice-latenz/README.md (Abschnitt Abnahme) |

## Ergebnis

| Reihe | p50 ms | p95 ms | max ms | Fehler |
|---|---|---|---|---|
| A Suche (nice 0) | 286,9 | 547,1 | 5000,0 | 1 |
| B Suche (nice 10) | 275,0 | 554,3 | 2349,5 | 0 |
| A status.php | 28,8 | 42,0 | 1645,9 | 0 |
| B status.php | 28,5 | 40,0 | 69,8 | 0 |

Die Planerwartung "Suche B niedriger" trat für p50/p95 nicht ein; nur der Ausreißer fehlt in B. status.php wie erwartet unverändert (cgroup-Grenze).

## Deviations from Plan

- **[Rule 3 - Blocking] Registry-Port 5055 statt 5000:** Port 5000 gehört dem Connector-Stack (nc-mcp-exapp-registry), der nicht gestört werden durfte.
- **[Rule 3 - Blocking] CPU-Grenze für den ExApp-Container:** Ohne `--cpus 1` hätte ein einzelner OCR-Slot auf 12 vCPU keine Konkurrenz erzeugt, die Probe hätte nichts gemessen. Im README und in raw/machine.txt benannt.
- **Harness NC 34 statt "nc35":** Der Plan nennt den nc35-Harness, verweist aber auf compose-harp.yaml (NC 34.0.3). Die nc35-Container gehören dem Connector-Projekt; genutzt wurde compose-harp.yaml.
- **Companion in beiden Varianten = php/ vom Stand 46572f4d:** Im Sparsam-Lane "all" bleibt der OCR-Anspruch in beiden bei 2 Zeilen, der Unterschied ist damit nice.
- Harness nach der Messung abgebaut (Container, Volumes, Netz, Registry, Vorproxy); die Abbilder latA/latB bleiben lokal für eine Wiederholung. Hilfsskripte liegen ungetrackt unter .dev/latency/.

## Checkpoint-Ausgang (Task 3)

- Owner-Signal, wörtlich (28./29.09.2026, per AskUserQuestion, vom Koordinator übermittelt): "Abnehmen (Empfohlen)".
- Abgenommene Lesart, wörtlich: "Befund ist ehrlich und brauchbar; nice beseitigt genau die Haenger aus Issue #19 (max-Werte, Zeitdeckel-Fehler), auch wenn p50/p95 gleich bleiben. Die #19-Antwort kann spaeter darauf aufbauen, ein Entwurf erst auf gesonderten Auftrag."
- Im README unter "Abnahme" eingetragen, mit dem Hinweis, dass die Hänger-Aussage auf je einem Ausreißer aus einem Lauf beruht.
- Kein Antwortentwurf angelegt (Owner: erst auf gesonderten Auftrag), nichts auf Issue #19 gepostet, nichts gepusht.
- D-26-12 Teil 2 ist damit gemessen und abgenommen.

## Self-Check: PASSED

- Dateien vorhanden: scripts/ops/latency_probe.py, backend/tests/test_latency_probe.py, README und 6 Rohdateien
- Commits vorhanden: fb124643, 5f754064, b3daaa33, 8e65b37d (Zwischenstand), Abschlusscommit mit Abnahme
