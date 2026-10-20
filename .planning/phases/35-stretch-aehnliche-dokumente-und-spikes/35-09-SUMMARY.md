---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 09
subsystem: messung-str02
tags: [granite, e5, modellqualitaet, quantisierung, latenz, amd64, image]
status: komplett
requires: [35-03, 35-08]
provides:
  - "scripts/dev/model_quality.py: --pooling {mean,cls} (Standard mean), cls_pool, Pad-Token-Rückfall auf tokenizer_config.json"
  - "docs/measurements/2026-10-granite-vergleich/skripte/ 00 bis 05 (+03b) unter NARROW_SCOPE_DIRS"
  - "docs/measurements/2026-10-granite-vergleich/rohdaten/ 01 bis 05: Artefakte, int8-Build, Qualität de/en/fr, Positivkontrolle, Gegenprobe ort 1.31, amd64-Latenz, Image-Zuwachs"
affects: [35-10, 35-11]
tech-stack:
  added: []
  patterns: ["Rohdaten maskieren das Scratch-Verzeichnis als WORK", "Messläufe im ausgelieferten Image mit --network none"]
key-files:
  created:
    - docs/measurements/2026-10-granite-vergleich/skripte/00-ablauf.md
    - docs/measurements/2026-10-granite-vergleich/skripte/01-artefakte.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/02-int8.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/03-qualitaet.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/03b-gegenprobe-ort131.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/04-latenz-amd64.sh
    - docs/measurements/2026-10-granite-vergleich/skripte/04-anfrage-latenz.py
    - docs/measurements/2026-10-granite-vergleich/skripte/05-image-zuwachs.sh
    - docs/measurements/2026-10-granite-vergleich/rohdaten/ (21 Dateien)
  modified:
    - scripts/dev/model_quality.py
    - backend/tests/test_model_quality.py
    - backend/tests/test_measurement_scripts.py
    - docs/measurements/2026-10-granite-vergleich/README.md (nur neuer Abschnitt "Abweichungen vom Rezept")
decisions:
  - "Qualitätsläufe im ausgelieferten Image 1.4.3 (onnxruntime 1.30.0); Gegenprobe mit 1.31.0 aus uv.lock ergibt identische Ränge je Fall"
  - "Einzelanfrage-Latenz beider Modelle über eigenes onnxruntime-Skript statt Suchpfad (Wrapper e5-fest, kein Produktcode-Diff)"
  - "Speichergrenze 4 GB auf die Mess-VM bezogen (6,2 GB verfügbar), Host 3,0 GB frei; dokumentiert als Abweichung 6"
metrics:
  duration: "ca. 45 min"
  completed: 2026-10-20
  tasks_done: 3
  tasks_total: 3
---

# Phase 35 Plan 09: granite-Vergleich lokal (STR-02) Summary

CLS-Schalter im Messwerkzeug, granite-Artefakte der Revision `835ad140` sha256-geprüft, eigener int8-Build zweimal byte-gleich (97.858.099 Byte), Qualität beider Modelle in de/en/fr aus einem Lauf, amd64-Latenz und Image-Zuwachs gemessen; ausgeliefertes Modell bleibt e5-small.

## Commits

| Task | Name | Commit |
|---|---|---|
| 1 (RED) | Tests für Pooling-Schalter | 97da4f25 |
| 1 (GREEN) | CLS pooling switch, GRANITE_RUN_DIR, 00-ablauf.md | 5260144b |
| 2 | Artefakte, int8-Build, Qualitätsläufe | 5c7f7de0 |
| 3 | amd64-Latenz, Image-Zuwachs | fd28c6ce |

## Kernzahlen

**Qualität (MRR, 512 Token, Image 1.4.3, `--network none`)**

| Sprache | e5 int8 | e5 fp32 | granite int8 | granite fp32 | granite IBM-int8 |
|---|---:|---:|---:|---:|---:|
| de (120) | 0,4428 | 0,4807 | 0,5279 | 0,6422 | 0,5051 |
| en (42) | 0,5010 | 0,4647 | 0,5515 | 0,5796 | 0,5668 |
| fr (120) | 0,2604 | 0,2870 | 0,3397 | 0,4658 | 0,3662 |

Recall@1/@5 und Ränge je Fall in `rohdaten/03-qualitaet-*.txt`. Paarvergleich, Vorzeichentest und Verdikt folgen in 35-11.

**Positivkontrolle** (granite int8, mean gegen cls, MRR): de 0,3582 gegen 0,5279; en 0,4981 gegen 0,5515; fr 0,3148 gegen 0,3397. mean überall schlechter, der Schalter greift.

**Plausibilität:** e5 fp32 en 0,4647 und fr 0,2870 gleich den Septemberzahlen; Gegenprobe onnxruntime 1.31.0 (uv.lock) gegen 1.30.0 (Image): alle Ränge je Fall identisch.

**amd64** (i5-1335U, cpuset 2,3, 2 Threads, Image 1.4.3):

| Modell | Token/s p50 | kalt p50 / max | warm p50 / p95 |
|---|---:|---:|---:|
| e5 int8 | 3624,2 | 1368,1 / 1778,7 ms | 3,19 / 4,04 ms |
| granite int8 | 2880,8 | 1370,6 / 1888,9 ms | 4,19 / 5,25 ms |

**Image-Zuwachs** für granite neben e5: 123.186.163 Byte unkomprimiert, 71.125.848 Byte gzip (Modell 97,9 MB / 67,1 MB, Tokenizer 25,3 MB / 4,0 MB).

**Produktdiff:** `git diff --stat 3d4eca60..HEAD -- backend/src backend/Dockerfile backend/appinfo` ist leer.

## Deviations from Plan

1. **[Rule 3] Push und CI-Block nicht ausgeführt.** Paralleler Worktree-Lauf; Push und CI übernimmt der Orchestrator.
2. **Tokenizer-sha256 nicht voll im README.** Geprüft gegen Größe und Präfix/Suffix aus 35-RESEARCH plus Hub-`x-linked-etag`; voller Wert in `rohdaten/01-artefakte.txt` (README-Abweichung 1).
3. **onnxruntime-Version.** README Abschnitt 2 sagt "heute 1.31.0", Image 1.4.3 trägt 1.30.0. Hauptlauf im Image wie vorgeschrieben, Zusatzskript `03b-gegenprobe-ort131.sh` mit 1.31.0: identische Ränge (README-Abweichung 2).
4. **granite bei 1024 Token nicht gemessen.** Werkzeug hat keinen Längenschalter (README-Abweichung 3).
5. **Einzelanfrage-Latenz über eigenes Skript `04-anfrage-latenz.py`** statt Suchpfad, weil der Produkt-Wrapper e5-fest ist (README-Abweichung 5). Durchsatz unverändert über `findling.embed.bench`.
6. **Speicher:** Host 3,0 GB frei (unter den 4 GB aus README Abschnitt 4), Mess-VM 6,2 GB verfügbar, kein Swap in der VM, 1-GB-Abbruchgrenze nie erreicht (README-Abweichung 6).
7. **Kein Probe-Image**, Lizenztext durch `COPYING.sqlite-vec` (Apache-2.0) vertreten (README-Abweichung 7).
8. **[Rule 1] Gate `schluesselwort-mit-wert`** fand die Variable `token` in `04-anfrage-latenz.py`; umbenannt (reines Umbenennen), danach Schritt 4 neu gefahren, damit Skript und Rohdatei zusammengehören.
9. **Zusätzlich gemessen:** e5 fp32 von der Dockerfile-Revision (sha256 gegen Dockerfile), IBM-int8 als Vergleichspunkt, obwohl A2 hielt (README Abschnitt 3 sieht ihn vor).
10. **Rohdaten maskiert:** das Scratch-Verzeichnis steht als `WORK`, damit kein Maschinenpfad ins öffentliche Repo kommt.

## TDD Gate Compliance

RED `97da4f25` (5 failed, 37 passed), GREEN `5260144b` (42 passed). Kein Refactor nötig.

## Known Stubs

Keine. Tabellen und Verdikt im README entstehen planmäßig in 35-11, arm64 in 35-10.

## Gates

ruff check und format (backend und `../scripts`, dazu `04-anfrage-latenz.py`), pyright 0 errors, vulture, reuse lint grün; `test_model_quality`, `test_measurement_scripts`, `test_public_artifacts` grün (609 passed). Volle Suite: siehe Nachtrag unten.

## Self-Check: PASSED

- 8 Skripte und 21 Rohdateien unter `docs/measurements/2026-10-granite-vergleich/` im Repo, keine `.onnx`
- Commits 97da4f25, 5260144b, 5c7f7de0, fd28c6ce im Log
- Kein Diff unter backend/src, backend/Dockerfile, backend/appinfo

## Threat Flags

Keine neue Angriffsfläche. Modellartefakte nur aus festgenagelter Revision mit sha256-Abbruch (T-35-SC); keine `.onnx` im Repo; uv.lock unverändert (die `quantize`-Gruppe `onnx==1.23.2` aus dem Lockfile wurde lokal synchronisiert).
