---
phase: 22-messanfahrt-bl-f03
plan: 01
subsystem: messwerkzeuge
tags: [ops, cgroup, ocr, ci, arm64, messung]
requires: []
provides:
  - "W1 scripts/ops/cpu_sampler.sh (Kernbelegung aus cpu.stat, für B1/B6)"
  - "W2 scripts/ops/proc_anon_sampler.sh (RssAnon/VmHWM je Prozess, für B2)"
  - "W3 scripts/ops/ocr_slot_probe.py (Slot-Probe über ExtractionWorker, für B3/B4/W4)"
  - "W4 Job slots in .github/workflows/measure.yml mit F4-Definition (Grundlage D-03)"
affects:
  - "22-06 (CI-Lauf von W4 nach Push-Freigabe)"
  - "Rechenblatt der Box-Anfahrt (F4 gegen Schwelle 1,5)"
tech-stack:
  added: []
  patterns:
    - "cgroup-Lesen statt Docker-Client, beide Treiber-Layouts, Verweigerung statt Nullen"
    - "später findling-Import in scripts/ops, Ausnahme im Test namentlich benannt"
    - "Wegwerf-Container desselben Digests mit --network none und gemountetem Skript"
key-files:
  created:
    - scripts/ops/cpu_sampler.sh
    - scripts/ops/proc_anon_sampler.sh
    - scripts/ops/ocr_slot_probe.py
  modified:
    - backend/tests/test_ops_scripts.py
    - .github/workflows/measure.yml
decisions:
  - "F4 = Median Seiten je Sekunde bei N=4 auf cpuset 0-3 geteilt durch N=1 auf cpuset 0, drei Runden; fehlender Wert oder verlorener Slot ergibt 'F4 unbestimmt' mit Fehler"
  - "W3 zählt einen abgeschnittenen (truncated) oder fehlgeschlagenen Slot als verlorenen Slot, seine Seiten gehen nicht in die Seitenrate ein"
  - "W3 fährt vor der ersten gezählten Runde einen ungezählten Vorlauf je Worker, damit Kindstart und Importe nicht Runde 1 belasten"
  - "pypdfium2 ist neben findling die zweite benannte Import-Ausnahme von W3 (Modus single rendert die Seite wie findling.extract.raster)"
metrics:
  duration: "ca. 12 min"
  completed: 2026-09-25
  tasks: 3
  files: 5
---

# Phase 22 Plan 01: Messwerkzeuge W1 bis W4 Summary

Drei boxlose Messwerkzeuge unter scripts/ops (CPU-Sampler aus cgroup cpu.stat, Anon-Sampler je Prozess ohne Argumentliste, OCR-Slot-Probe über den echten ExtractionWorker) samt Tests, dazu ein eigener arm64-Job in measure.yml, der W3 für N=1,2,4, embed.bench mit 1,2,4 Threads und B7 fährt und F4 vorab definiert berechnet.

## Aufgaben

| Task | Name | Commit | Dateien |
| ---- | ---- | ------ | ------- |
| 1 | W1 cpu_sampler.sh und W2 proc_anon_sampler.sh mit Tests | aa56d76 | scripts/ops/cpu_sampler.sh, scripts/ops/proc_anon_sampler.sh, backend/tests/test_ops_scripts.py |
| 2 | W3 ocr_slot_probe.py mit Tests | 8234aed | scripts/ops/ocr_slot_probe.py, backend/tests/test_ops_scripts.py |
| 3 | W4-Job und B7 in measure.yml, F4 definiert | b8448e4 | .github/workflows/measure.yml |

## Was entstanden ist

- **W1 cpu_sampler.sh:** Präfix `findling-cpu`, Pfadbildung für systemd und cgroupfs wie rss_sampler.sh, vor jedem Lesen `[ ! -r "$CGROUP/cpu.stat" ]`, Schlusszeile `summary samples= mean_cores= max_cores= reason=` mit Grund `cgroup gone` oder `signal`. Rauchtest mit gestagter cgroup: drei Proben, Wegfall der cgroup endet mit Schlusszeile.
- **W2 proc_anon_sampler.sh:** Präfix `findling-anon`, im Container läuft nur `grep` über `/proc/[0-9]*/status` für Name, RssAnon, VmHWM; Auswertung auf dem Wirt; Schlusszeile mit Maximum RssAnon je Prozessname. Prozessnamen mit Leerzeichen oder Komma bleiben CSV-fest (zeilenweise Schleife, Komma wird Unterstrich).
- **W3 ocr_slot_probe.py:** Modi `slots` und `single`, Argumente `--slots --rounds --scan --pages --mode --timeout`; Ausgabe `arch`, `cpus_visible`, `slots`, `round ... failed_slots`, `pages_per_second_median`; im Modus single `omp_limit_1` und `omp_unset` mit Wandzeit und cgroup-CPU-Zeit, dazu `omp_env_preset`. Rückgabe 2 bei falschen Argumenten, 1 bei einem verlorenen Slot.
- **W4 Job `slots`:** Scan aus `_scan_pdf(Rng("phase-22-w4", "scan-8"), 8)` mit Größe und SHA-256 in scan.txt, W3 N=1/2/4, W3 single, embed.bench `--batch 2 --sequence 512 --threads 1/2/4`, B7 über `measure_compounds_nl.sh`, F4-Schritt (läuft auch bei B7-Fehler), Artefakt `w4-arm64` (Upload auch nach Fehlschritten). Job `measure` ist unverändert (Diff reine Anfügung ab Zeile 413).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Korrektheit] W1-CSV hat eine fünfte Spalte uptime_usec**
- **Found during:** Task 1
- **Issue:** Mit `date +%s` allein ist die Wandzeit je Takt sekundengenau; bei 5 s Takt wäre die maximale Kernbelegung bis zu 20 Prozent falsch.
- **Fix:** Spalte `uptime_usec` aus /proc/uptime angehängt; die vier Planspalten stehen unverändert davor, die Schlusszeile rechnet mit dieser Uhr.
- **Commit:** aa56d76

**2. [Rule 3 - Blockierend] Zweite Import-Ausnahme pypdfium2 in W3**
- **Found during:** Task 2
- **Issue:** Modus single braucht eine gerenderte Seite; `findling.extract.raster.render_page_png` nimmt ein pypdfium2-Dokument. Der Plan nannte nur findling als Ausnahme.
- **Fix:** pypdfium2 wird wie findling erst in der Funktion importiert; der Test benennt beide Ausnahmen (`OCR_SLOT_PROBE_PACKAGES`) und prüft, dass auf Modulebene nur Standardbibliothek steht. Ein zusätzlicher Test lädt die Probe in einem frischen Interpreter und belegt, dass Laden plus Argumentabweisung findling nicht importiert.
- **Commit:** 8234aed

**3. [Rule 2 - Korrektheit] F4 prüft zusätzlich verlorene Slots**
- **Found during:** Task 3
- **Issue:** Ohne pipefail maskiert `tee` die Rückgabe 1 der Probe; ein Lauf mit fehlgeschlagenem Slot hätte trotzdem einen F4-Wert geliefert.
- **Fix:** Der F4-Schritt zählt Runden mit `failed_slots` ungleich 0 und schreibt dann `F4 unbestimmt` mit Fehler.
- **Commit:** b8448e4

### Zustandsdateien

- `requirements.mark-complete MESS-07` hat MESS-07 abgehakt, obwohl 22-01 nur die Werkzeuge liefert und die Box-Anfahrt noch aussteht. Zurückgenommen, REQUIREMENTS.md bleibt unverändert; MESS-07 schließt erst die Anfahrt.
- Die SDK-Befehle haben STATE.md mit Gedankenstrichen und veralteten Texten beschädigt; von Hand nachgezogen (Position, Fortschritt, nächster Schritt, Metrikzeile, zwei Entscheidungen, Sitzung). Die ROADMAP-Zeile von Phase 22 wurde auf das Tabellenformat gebracht.

### Hinweis zu T-22-04

Der B7-Container (python:3.13-slim-trixie aus measure_compounds_nl.sh) läuft nicht mit `--network none`, weil er die gepinnte niederländische Wortliste und tantivy per apt/pip installiert. Er ist nicht das Produktabbild und sieht keine Produktdaten und kein Geheimnis; im Workflow als Kommentar begründet. Jeder docker run des Produktabbilds im Job trägt `--network none` (Zähler 10 auf 16).

## Verification

- `ruff check .`, `ruff format --check .`, pyright (latest) 0 Fehler, vulture sauber, ruff check/format für ../scripts grün
- pytest tests/test_ops_scripts.py tests/test_workflow_pins.py tests/test_measurement_scripts.py: 481 passed
- rss_sampler.sh unverändert; beide Shell-Skripte und die Probe mit Modus 100755 im Index
- YAML-Prüfung `jobs.slots.runs-on == ubuntu-24.04-arm`; F4-Logik mit gestagten Dateien lokal geprobt (2.625; unbestimmt bei verlorenem Slot; unbestimmt bei fehlender Datei)
- Kein Lauf auf AWS, kein Push. Der CI-Lauf von W4 folgt in 22-06.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: scripts/ops/cpu_sampler.sh, scripts/ops/proc_anon_sampler.sh, scripts/ops/ocr_slot_probe.py
- FOUND: aa56d76, 8234aed, b8448e4
