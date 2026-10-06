---
phase: 25-einbettungsspur-und-modellwahl
plan: 01
subsystem: embeddings
tags: [onnxruntime, e5-small, fp32, messung, github-release, immutable-release]

requires: []
provides:
  - "FP32_EXTRA_BYTES = 367 * MIB (384827392 Byte), gemessen im Abbild :dev"
  - "Einbettungsrate fp32 gegen int8: Verhältnis 0,55 (Median 3,220 gegen 5,901 Passagen je s)"
  - "Unveränderliches Release model-e5-small-fp32-614241f mit Asset multilingual-e5-small-fp32-614241f.onnx, Digest ca456c06...8665 gegengeprüft"
affects: [25-08, 25-11, ram-schranke, einbettungsspur, modellwahl]

tech-stack:
  added: []
  patterns:
    - "Release-Gegenprobe: Kopfzeilen, GitHub-API-Metadaten und vollständiger Download mit zwei Hash-Werkzeugen"

key-files:
  created:
    - docs/measurements/2026-09-fp32-speicher/README.md
    - docs/measurements/2026-09-fp32-speicher/release-notes.md
    - docs/measurements/2026-09-fp32-speicher/skripte/01-fp32-speicher.py
    - docs/measurements/2026-09-fp32-speicher/rohdaten/00-umgebung.txt
    - docs/measurements/2026-09-fp32-speicher/rohdaten/01-int8-lauf1.txt bis -lauf5.txt
    - docs/measurements/2026-09-fp32-speicher/rohdaten/01-fp32-lauf1.txt bis -lauf5.txt
    - docs/measurements/2026-09-fp32-speicher/rohdaten/02-release-gegenprobe.txt
  modified: []

key-decisions:
  - "FP32_EXTRA_BYTES aus größtem fp32-Wert minus kleinstem int8-Wert nach dem ersten Batch, aufgerundet auf 367 MiB"
  - "Upload auf Delegation des Owners durch die Orchestrator-Sitzung; Executor hat nur gegengeprüft, nichts hochgeladen oder gepusht"

patterns-established:
  - "Gegenprobe mit anderem Muster als die Umsetzung: API-Metadaten plus certutil neben sha256sum"

requirements-completed: [MOD-02]

duration: Fortsetzung nach Checkpoint, Task 3 rund 10 min
completed: 2026-09-28
---

# Phase 25 Plan 01: fp32-Speichermessung und Modell-Release Summary

**fp32-Mehrbedarf von e5-small im Abbild gemessen (FP32_EXTRA_BYTES = 367 * MIB), und das fp32-Asset liegt unveränderlich unter der festen Release-URL mit dem gepinnten sha256.**

## Performance

- **Fortsetzung:** Task 3 nach dem human-action-Checkpoint, 28.09.2026 ab 11:50 UTC
- **Tasks:** 3 von 3
- **Dateien in Task 3:** 2 (README.md ergänzt, eine Rohdatei neu)

## Accomplishments

- Zehn Messläufe (je fünf int8 und fp32, frische Container, RssAnon); Speicherstreuung unter 0,3 Prozent
- `FP32_EXTRA_BYTES = 367 * MIB` (384827392 Byte) abgeleitet, Übernahme als Literal in Plan 25-08
- Release `model-e5-small-fp32-614241f`: 302 auf `release-assets.githubusercontent.com`, `immutable: true`, ein Asset mit 470268510 Byte, "Latest" bleibt `v1.3.0`; vollständiger Download mit `sha256sum` und `certutil` gleich dem Pin

## Task Commits

1. **Task 1: fp32-Datei beschaffen, prüfen, im Abbild messen** - `bf40a64`
2. **Task 2: Auswertung, FP32_EXTRA_BYTES, Release-Text** - `49de3fb`
3. **Task 3: Release (Upload durch Orchestrator auf Owner-Delegation), Gegenprobe im README** - `a330ef9` (docs)

## Deviations from Plan

**1. Upload nicht durch den Owner selbst, sondern delegiert**
- Der Plan sah den Upload als Owner-Handlung vor. Der Owner hat ihn an die Orchestrator-Sitzung delegiert ("kannst du das übernehmen?"). Immutability wurde vor dem Anlegen per API eingeschaltet, das Release als Entwurf mit Asset angelegt und dann veröffentlicht. Der Executor hat nichts hochgeladen oder gepusht; im README als Herkunft vermerkt.

**2. Nachläufe in Task 1** (bereits in Task 2 dokumentiert): Die Rate streute über 5 Prozent, daher je zwei Läufe mehr, alle zehn in der Tabelle.

**3. Worktree-Basis korrigiert:** Der Worktree stand beim Start auf einem alten Stand (`cce78ab`); per Startprüfung auf die erwartete Basis `5542684` gesetzt. Keine lokalen Änderungen gingen verloren.

## Verification

- `curl -sI` auf die Asset-URL: `HTTP/1.1 302 Found`, Location-Host `release-assets.githubusercontent.com`
- Download: Status 200, 470268510 Byte, sha256 `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665` (zwei Werkzeuge), Prüfdatei gelöscht
- `backend/tests/test_public_artifacts.py`: 55 passed, keine neue Ausnahme nötig
- Keine `.onnx`-Datei im Repo; keine Em- oder En-Dashes in README und Rohdatei

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: docs/measurements/2026-09-fp32-speicher/rohdaten/02-release-gegenprobe.txt
- FOUND: docs/measurements/2026-09-fp32-speicher/README.md (Abschnitt 6. Release)
- FOUND: bf40a64, 49de3fb, a330ef9
